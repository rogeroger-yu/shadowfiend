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
from shadowfiend.processor import service

from tooz import coordination

CONF = cfg.CONF
LOG = log.getLogger(__name__)

cfg.CONF.import_group('processor', 'shadowfiend.processor.config')
process_period = CONF.processor.process_period


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
        #self.fetch = service.fetcher

    def start(self, *args, **kwargs):
        super(ProcessorService, self).start(*args, **kwargs)
        LOG.debug("Waiting for process")

        if self.periodic_enable:
            if self.periodic_fuzzy_delay:
                initial_delay = random.randint(0, self.periodic_fuzzy_delay)
            else:
                initial_delay = None

            pt = ProcessorPeriodTasks(CONF)
            self.tg.add_dynamic_timer(pt.run_periodic_tasks,
                                      initial_delay=initial_delay,
                                      periodic_interval_max=
                                      self.periodic_interval_max,
                                      context=None)


class ProcessorPeriodTasks(periodic_task.PeriodicTasks):
    def __init__(self, conf):
        super(ProcessorPeriodTasks, self).__init__(conf)
        # keysteon fetcher
        self.keystone_fetcher = service.fetcher.KeystoneFetcher()

        # gnocchi fetcher
        self.gnocchi_fetcher = service.fetcher.GnocchiFetcher()

        # services test fetcher
        #self.cinder_fetcher = service.fetcher.CinderFetcher()
        #self.nova_fetcher = service.fetcher.NovaFetcher()
        #self.glance_fetcher = service.fetcher.GlanceFetcher()
        self.neutron_fetcher = service.fetcher.NeutronFetcher()

        # DLM
        self.coord = coordination.get_coordinator(
            CONF.processor.coordination_url,
            str(uuid.uuid4()).encode('ascii'))
        self.coord.start()

    def _lock(self, tenant_id):
        lock_name = b"shadowfiend-" + str(tenant_id).encode('ascii')
        return self.coord.get_lock(lock_name)

    def _check_state(self, tenant_id):
        timestamp = self.gnocchi_fetcher.get_state(tenant_id)
        LOG.debug("timestamp is :%s" % timestamp)
        if not timestamp:
            month_start = timeutils.get_month_start()
            return timeutils.dt2ts(month_start)

        now = timeutils.utcnow_ts()
        next_timestamp = timestamp + CONF.processor.process_period
        wait_time = CONF.processor.process_period
        if next_timestamp + wait_time < now:
            return next_timestamp
        return 0

    @periodic_task.periodic_task(run_immediately=True, spacing=process_period)
    @set_context
    def Primary_Period(self, ctx):
        LOG.info("************************")
        LOG.info("Processing the correspondence between tenants and accounts")
        
        #fetch billing enable tenants
        tenants = self.keystone_fetcher.get_rate_tenants()
        LOG.info("Tenants are %s" % str(tenants))

        import pdb;pdb.set_trace()
        #-----------------cinder client test---------------------------
        #self.cinder_fetcher.get_volumes(volume_id='0296d18e-32dc-4ce8-9d37-aa98979128fe')
        #self.nova_fetcher.flavor_list()
        #self.glance_fetcher.image_list()
        self.neutron_fetcher.networks_list('3427804b-70d9-4a99-9bac-39b6fbab0184')

        #-----------------cinder client test---------------------------

        self._check_state(tenants[0])


#        while len(tenants):
#            for tenant in tenants[:]:
#                lock = self._lock(tenant)
#                if lock.acquire(blocking=False):
#                    if not self._check_state(tenant):
#                        tenants.remove(tenant)
#                    else:
#                        worker = Worker(self.collector,
#                                        self.storage,
#                                        tenant)
#                        worker.run()
#                    lock.release()
#                self.coord.heartbeat()
#            # NOTE(sheeprine): Slow down looping if all tenants are
#            # being processed
#            eventlet.sleep(1)
#        # FIXME(sheeprine): We may cause a drift here
#        eventlet.sleep(CONF.collect.period)


        #check every tenant's timestamp is prepared, push into thread queue


        LOG.info("Process successfully in this period")
