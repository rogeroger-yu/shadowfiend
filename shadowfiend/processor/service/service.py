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
from shadowfiend.processor import service
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
        # self.fetch = service.fetcher

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
        self.keystone_fetcher = service.fetcher.KeystoneFetcher()
        self.gnocchi_fetcher = service.fetcher.GnocchiFetcher()

        # DLM
        self.coord = coordination.get_coordinator(
            CONF.processor.coordination_url,
            str(uuid.uuid4()).encode('ascii'))
        self.coord.start()

    def _lock(self, tenant_id):
        lock_name = b"shadowfiend-" + str(tenant_id).encode('ascii')
        return self.coord.get_lock(lock_name)

    def _check_state(self, tenant_id):
        timestamp = self.gnocchi_fetcher.get_state(
            tenant_id, 'shadowfiend', 'top')
        LOG.debug("timestamp is :%s" % timestamp)
        if not timestamp:
            LOG.debug("There is no shadowfiend timestamp"
                      "Initialization from cloudkitty's first record")
            timestamp = self.gnocchi_fetcher.get_state(
                tenant_id, 'cloudkitty', 'bottom')

        top_stamp = self.gnocchi_fetcher.get_state(
            tenant_id, 'cloudkitty', 'top')
        next_timestamp = timestamp + CONF.processor.process_period
        if next_timestamp < top_stamp:
            return next_timestamp
        return 0

    @periodic_task.periodic_task(run_immediately=True, spacing=process_period)
    @set_context
    def Primary_Period(self, ctx):
        LOG.info("************************")
        LOG.info("Processing the correspondence between tenants and accounts")

        # fetch rating enable tenants
        rate_tenants = self.keystone_fetcher.get_rate_tenants()
        LOG.info("Tenants are %s" % str(rate_tenants))

        while len(rate_tenants):
            for rate_tenant in rate_tenants[:]:
                lock = self._lock(rate_tenant)
                if lock.acquire(blocking=False):
                    begin = self._check_state(rate_tenant)
                    if not begin:
                        rate_tenants.remove(rate_tenant)
                    else:
                        worker = Worker(ctx, rate_tenant, begin)
                        worker.run()
                    lock.release()
                self.coord.heartbeat()
            # NOTE(sheeprine): Slow down looping if all tenants are
            # being processed
            eventlet.sleep(1)

        # check every tenant's timestamp is prepared, push into thread queue

        LOG.info("Process successfully in this period")


class Worker(object):
    def __init__(self, ctx, tenant_id, begin):
        self.begin = begin
        self.context = ctx
        self.tenant_id = tenant_id
        # self.period = CONF.processor.process_period
        self.gnocchi_fetcher = service.fetcher.GnocchiFetcher()
        self.keystone_fetcher = service.fetcher.KeystoneFetcher()
        self.conductor = conductor_api.API()

    def run(self):
        period_cost = self.gnocchi_fetcher.get_current_consume(
            self.tenant_id, self.begin)
        rate_user_id = self.keystone_fetcher.get_rate_user(self.tenant_id)
        if rate_user_id == []:
            LOG.error("There is no billing owner in you project: %s "
                      "Please contact the administrator" % self.tenant_id)
            raise ValueError("Not Found rate_user_id")
        account = self.conductor.get_account(
            self.context, rate_user_id)
        balance = account['balance']
        if account['owed'] and account['owed_at'] is not None:
            owed_offset = (timeutils.utcnow_ts -
                           timeutils.str2ts(account['owed_at']))
            if (owed_offset <= account['level'] * TS_DAY or
                    account['level'] == 9):
                pass
            else:
                self.owed_action(self.tenant_id)
        else:
            self.conductor.update_account(
                self.context,
                user_id=rate_user_id,
                balance=balance - period_cost)
        self.gnocchi_fetcher.set_state(self.tenant_id, self.begin)

    def owed_action(self, tenant_id):
        # get billing resource
        for _service in CONF.processor.services:
            try:
                resources = self.gnocchi_fetcher.get_resources(_service,
                                                               tenant_id)
                for resource in resources:
                    service_map[_service].drop_resource(_service,
                                                        resource['id'])
            except Exception as e:
                LOG.warning("Error while drop resource: %s: %s" %
                            (resource, e))
