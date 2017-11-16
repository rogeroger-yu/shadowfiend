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

from oslo_config import cfg
from oslo_db import options

from shadowfiend.common import paths


sql_opts = [
    cfg.StrOpt('mysql_engine',
               default='InnoDB',
               help='MySQL engine to use.')
]

_DEFAULT_SQL_CONNECTION = 'sqlite:///' + paths.state_path_def('shadowfiend.sqlite')


cfg.CONF.register_opts(sql_opts, 'database')
options.set_defaults(cfg.CONF, _DEFAULT_SQL_CONNECTION, 'shadowfiend.sqlite')
