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

import sys

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log
from oslo_reports import guru_meditation_report as gmr

from shadowfiend.common import service
from shadowfiend.common import version

from shadowfiend.conductor.handlers import account_api
from shadowfiend.conductor.handlers import project_api


LOG = log.getLogger(__name__)


def main():
    service.prepare_service(sys.argv)
    gmr.TextGuruMeditation.setup_autorun(version)

    cfg.CONF.import_opt('topic',
                        'shadowfiend.conductor.config',
                        group='conductor')

    managers = [
        account_api.Handler(),
        project_api.Handler(),
    ]

    server = service.Service.create(binary='shadowfiend-conductor',
                                    topic=cfg.CONF.conductor.topic,
                                    manager=managers)
    workers = cfg.CONF.conductor.workers or processutils.get_worker_count()
    service.serve(server, workers=workers)
    service.wait()


if __name__ == '__main__':
    main()
