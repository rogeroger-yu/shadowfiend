import sys

from oslo_config import cfg
from oslo_concurrency import processutils
from oslo_log import log
from oslo_reports import guru_meditation_report as gmr

from shadowfiend.common import config
from shadowfiend.common import service
from shadowfiend.common import version

from shadowfiend.conductor.handlers import account_api
from shadowfiend.conductor.handlers import project_api
from shadowfiend.conductor.handlers import usr_prj_api
from shadowfiend.conductor.handlers import charge_api


LOG = log.getLogger(__name__)


def main():
    service.prepare_service(sys.argv)
    gmr.TextGuruMeditation.setup_autorun(version)

    cfg.CONF.import_opt('topic', 'shadowfiend.conductor.config', group='conductor')

    managers = [
        account_api.Handler(),
        project_api.Handler(),
        usr_prj_api.Handler(),
        charge_api.Handler(),
    ]

    server = service.Service.create(binary='shadowfiend-conductor',
                                    topic=cfg.CONF.conductor.topic,
                                    manager=managers)
    workers = cfg.CONF.conductor.workers or processutils.get_worker_count()
    service.serve(server, workers=workers)
    service.wait()


if __name__ == '__main__':
    main()
