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

import os
from wsgiref import simple_server

from oslo_config import cfg
from oslo_log import log
from paste import deploy
import pecan

from shadowfiend.api import config as api_config
from shadowfiend.common import config as common_config
from shadowfiend.common.i18n import _LI


LOG = log.getLogger(__name__)

auth_opts = [
    cfg.StrOpt('api_paste_config',
               default="/home/heat-admin/shadowfiend/etc/shadowfiend/api_paste.ini",
               help="Configuration file for WSGI definition of API."
               ),
    cfg.StrOpt('auth_strategy',
               choices=['noauth', 'keystone'],
               default='keystone',
               help=("The strategy to use for auth. Supports noauth and "
                     "keystone")),
]

api_opts = [
    cfg.IPOpt('host_ip',
              default="0.0.0.0",
              help='Host serving the API.'),
    cfg.PortOpt('port',
                default=8686,
                help='Host port serving the API.'),
    cfg.BoolOpt('pecan_debug',
                default=False,
                help='Toggle Pecan Debug Middleware.'),
]

CONF = cfg.CONF
CONF.register_opts(auth_opts)
CONF.register_opts(api_opts, group='api')


def get_pecan_config():
    filename = api_config.__file__.replace('.pyc', '.py')
    return pecan.configuration.conf_from_file(filename)


def setup_app(config=None):

    if not config:
        config = get_pecan_config()

    app_conf = dict(config.app)
    common_config.set_middleware_defaults()

    app = pecan.make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}),
        **app_conf
    )

    return app


def load_app():
    cfg_file = None
    cfg_path = cfg.CONF.api_paste_config
    if not os.path.isabs(cfg_path):
        cfg_file = CONF.find_file(cfg_path)
    elif os.path.exists(cfg_path):
        cfg_file = cfg_path

    if not cfg_file:
        raise cfg.ConfigFilesNotFoundError([cfg.CONF.api_paste_config])
    LOG.info(_LI("Full WSGI config used: %s") % cfg_file)
    return deploy.loadapp("config:" + cfg_file)


def build_server():
    # Create the WSGI server and start it
    host = CONF.api.host_ip
    port = CONF.api.port
    LOG.info(_LI('Starting server in PID %s'), os.getpid())
    LOG.info(_LI("Configuration:"))

    if host == '0.0.0.0':
        LOG.info(_LI('serving on 0.0.0.0:%(sport)s, view at '
                     'http://127.0.0.1:%(vport)s'),
                 {'sport': port, 'vport': port})
    else:
        LOG.info(_LI("serving on http://%(host)s:%(port)s"),
                 {'host': host, 'port': port})

    server_cls = simple_server.WSGIServer
    handler_cls = simple_server.WSGIRequestHandler

    app = load_app()

    srv = simple_server.make_server(
        host,
        port,
        app,
        server_cls,
        handler_cls)

    return srv


def app_factory(global_config, **local_conf):
    return setup_app()
