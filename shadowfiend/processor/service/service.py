import functools
import random

from oslo_config import cfg
from oslo_log import log
from oslo_service import periodic_task

from shadowfiend.processor import service
from shadowfiend.common import context
from shadowfiend.common import service as rpc_service

CONF = cfg.CONF
LOG = log.getLogger(__name__)


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


def set_context(func):
    @functools.wraps(func)
    def handler(self, ctx):
        ctx = context.make_admin_context(all_tenants=True)
        context.set_ctx(ctx)
        func(self, ctx)
        context.set_ctx(None)
    return handler


cfg.CONF.import_opt('process_period', 'shadowfiend.processor.config', group='processor')
process_period = CONF.processor.process_period

class ProcessorPeriodTasks(periodic_task.PeriodicTasks):
    def __init__(self, conf):
        super(ProcessorPeriodTasks, self).__init__(conf)

    @periodic_task.periodic_task(run_immediately=True, spacing=process_period)
    @set_context
    def period_test(self, ctx):
        LOG.info("********************************************************************************")
        LOG.info("Processing the correspondence between tenants and accounts")
        
        #fetch billing enable tenants

        #check every tenant's timestamp is prepared, push into thread queue


        LOG.info("Process successfully in this period")






