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

OPT_GROUP = cfg.OptGroup(
    name='conductor',
    title='Options for the shadowfiend-conductor service')

SERVICE_OPTS = [
    cfg.StrOpt('topic',
               default='shadowfiend-conductor',
               help='The queue to add conductor tasks to.'),
    cfg.IntOpt(
        'workers',
        help=('Number of workers for OpenStack Conductor service.'
              'The default will be the number of CPUs available.')),
    cfg.IntOpt('conductor_life_check_timeout',
               default=4,
               help=('RPC timeout for the conductor liveness check that is '
                     'used for bay locking.')),
]


cfg.CONF.register_group(OPT_GROUP)
cfg.CONF.register_opts(SERVICE_OPTS, OPT_GROUP)
