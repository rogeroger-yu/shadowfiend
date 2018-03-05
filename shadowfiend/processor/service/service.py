# -*- coding: utf-8 -*-
# Copyright 2017 Openstack Foundation.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import eventlet
import functools
import random
import uuid

from oslo_config import cfg
from oslo_log import log
from oslo_service import periodic_task

from shadowfiend.common import context
from shadowfiend.common import service as rpc_service
from shadowfiend.common import timeutils
from shadowfiend.conductor import api as conductor_api
from shadowfiend.processor.service import fetcher
from shadowfiend.services import cinder
from shadowfiend.services import glance
from shadowfiend.services import neutron
from shadowfiend.services import nova

from tooz import coordination

CONF = cfg.CONF
LOG = log.getLogger(__name__)

cfg.CONF.import_group('processor', 'shadowfiend.processor.config')
process_period = CONF.processor.process_period

TS_DAY = 86400
service_map = {'computer': nova,
               'image': glance,
               'volume.volume': cinder,
               'volume.snapshot': cinder,
               'ratelimit.gw': neutron,
               'ratelimit.fip': neutron,
               'loadbalancer': neutron}


def set_context(func):
    @functools.wraps(func)
    def handler(self, ctx):
        ctx = context.make_admin_context(all_tenants=True)
        context.set_ctx(ctx)
        func(self, ctx)
        context.set_ctx(None)
    return handler


class ProcessorService(rpc_service.Service):
    def __init__(self, *args, **kwargs):
        super(ProcessorService, self).__init__(*args, **kwargs)

    def start(self, *args, **kwargs):
        super(ProcessorService, self).start(*args, **kwargs)
        LOG.debug("Waiting for process")

        if self.periodic_enable:
            if self.periodic_fuzzy_delay:
                initial_delay = random.randint(0, self.periodic_fuzzy_delay)
            else:
                initial_delay = None

            pt = ProcessorPeriodTasks(CONF)
            self.tg.add_dynamic_timer(
                pt.run_periodic_tasks,
                initial_delay=initial_delay,
                periodic_interval_max=self.periodic_interval_max,
                context=None)


class ProcessorPeriodTasks(periodic_task.PeriodicTasks):
    def __init__(self, conf):
        super(ProcessorPeriodTasks, self).__init__(conf)
        # Fetcher init
        self.keystone_fetcher = fetcher.KeystoneFetcher()
        self.gnocchi_fetcher = fetcher.GnocchiFetcher()

        # DLM
        self.coord = coordination.get_coordinator(
            CONF.processor.coordination_url,
            str(uuid.uuid4()).encode('ascii'))
        self.coord.start()
        self.conductor = conductor_api.API()

        self.tools = {'conductor': self.conductor,
                      'gnocchi_fetcher': self.gnocchi_fetcher,
                      'keystone_fetcher': self.keystone_fetcher}

    def _lock(self, project_id):
        lock_name = b"shadowfiend-" + str(project_id).encode('ascii')
        return self.coord.get_lock(lock_name)

    def _check_state(self, project_id):
        timestamp = self.gnocchi_fetcher.get_state(
            project_id, 'shadowfiend', 'top')
        LOG.debug("timestamp is :%s" % timestamp)
        if not timestamp and CONF.processor.historical_expenses:
            LOG.debug("There is no shadowfiend timestamp"
                      "Initialization from cloudkitty's first record")
            timestamp = self.gnocchi_fetcher.get_state(
                project_id, 'cloudkitty', 'bottom')
        elif not timestamp:
            LOG.debug("There is no shadowfiend timestamp"
                      "Initialization from current time")
            now_ts = timeutils.utcnow_ts()
            timestamp = now_ts - (now_ts % 3600)
            return timestamp

        top_stamp = self.gnocchi_fetcher.get_state(
            project_id, 'cloudkitty', 'top')
        next_timestamp = timestamp + CONF.processor.cloudkitty_period
        if next_timestamp < top_stamp:
            return next_timestamp
        return 0

    @periodic_task.periodic_task(run_immediately=True, spacing=process_period)
    @set_context
    def primary_period(self, ctx):
        # fetch rating enable projects
        rate_projects = self.keystone_fetcher.get_rate_projects()
        LOG.info("projects are %s" % str(rate_projects))

        while len(rate_projects):
            for rate_project in rate_projects[:]:
                lock = self._lock(rate_project)
                if lock.acquire(blocking=False):
                    begin = self._check_state(rate_project)
                    if not begin:
                        rate_projects.remove(rate_project)
                    else:
                        worker = Worker(ctx, rate_project, begin, self.tools)
                        worker.run()
                    lock.release()
                self.coord.heartbeat()
            # NOTE(sheeprine): Slow down looping if all projects are
            # being processed
            eventlet.sleep(1)

        # check every project's timestamp is prepared, push into thread queue
        LOG.info("Process successfully in this period")


class Worker(object):
    def __init__(self, context, project_id, begin, tools):
        self.context = context
        self.project_id = project_id
        self.begin = begin

        self.conductor = tools['conductor']
        self.gnocchi_fetcher = tools['gnocchi_fetcher']
        self.keystone_fetcher = tools['keystone_fetcher']

    def run(self):
        period_cost = self.gnocchi_fetcher.get_current_consume(
            self.project_id, self.begin)
        # get billing owner
        rate_user_id = self.keystone_fetcher.get_rate_user(
            self.project_id)
        if rate_user_id == []:
            LOG.error("There is no billing owner in you project: %s "
                      "Please contact the administrator" % self.project_id)
            raise ValueError("Not Found rate_user_id")
        try:
            account = self.conductor.get_account(
                self.context, rate_user_id)
        except Exception as e:
            LOG.error("Account: %s need to be registered to the "
                      "shadowfiend's database. The reason is: %s" %
                      (rate_user_id, e))
            raise
        if account['owed']:
            owed_offset = (timeutils.utcnow_ts() -
                           timeutils.str2ts(account['owed_at']))
            if (owed_offset <= account['level'] * TS_DAY or
                    account['level'] == 9 or not CONF.allow_owe_action):
                pass
            else:
                self.owed_action(self.project_id)
        self.conductor.update_account(
            self.context,
            user_id=rate_user_id,
            project_id=self.project_id,
            consumption=period_cost)
        self.gnocchi_fetcher.set_state(self.project_id, self.begin)

    def owed_action(self, project_id):
        # get billing resource
        for _service in CONF.processor.services:
            try:
                resources = self.gnocchi_fetcher.get_resources(_service,
                                                               project_id)
                for resource in resources:
                    service_map[_service].drop_resource(_service,
                                                        resource['id'])
            except Exception as e:
                LOG.error("Error while drop resource: %s: %s" %
                          (resource, e))
                raise
