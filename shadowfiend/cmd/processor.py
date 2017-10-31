import sys

from oslo_config import cfg
from oslo_concurrency import processutils
from oslo_log import log
from oslo_reports import guru_meditation_report as gmr

from shadowfiend.common import config
from shadowfiend.common import service as oslo_service
from shadowfiend.common import version

from shadowfiend.processor.service import service
from shadowfiend.processor.handlers import account_api
from shadowfiend.processor.handlers import project_api
from shadowfiend.processor.handlers import usr_prj_api
from shadowfiend.processor.handlers import charge_api


LOG = log.getLogger(__name__)


def main():
    oslo_service.prepare_service(sys.argv)
    gmr.TextGuruMeditation.setup_autorun(version)

    cfg.CONF.import_opt('topic', 'shadowfiend.processor.config', group='processor')

    managers = [
        account_api.Handler(),
        project_api.Handler(),
        usr_prj_api.Handler(),
        charge_api.Handler(),
    ]

    server = service.ProcessorService.create(binary='shadowfiend-processor',
                                             topic=cfg.CONF.processor.topic,
                                             manager=managers)
    workers = cfg.CONF.processor.workers or processutils.get_worker_count()
    oslo_service.serve(server, workers=workers)
    oslo_service.wait()


if __name__ == '__main__':
    main()
