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

# Register options for the service
CONF = cfg.CONF

OPTS = [
    cfg.BoolOpt('notify_account_charged',
                default=False,
                help="Notify user when he/she charges"),
    cfg.StrOpt('precharge_limit_rule',
               default='5/quarter',
               help='Frequency of do precharge limitation'),
    cfg.ListOpt('regions',
                default=['RegionOne'],
                help="A list of regions that is avaliable"),
    cfg.BoolOpt('enable_invitation',
                default=False,
                help="Enable invitation or not"),
    cfg.StrOpt('min_charge_value',
               default='0',
               help="The minimum charge value if meet the reward condition"),
    cfg.StrOpt('limited_accountant_charge_value',
               default=100000,
               help="The minimum charge value the accountant can operate"),
    cfg.StrOpt('limited_support_charge_value',
               default=200,
               help="The minimum charge value the support staff can operate"),
    cfg.StrOpt('reward_value',
               default='0',
               help="The reward value if meet the reward condition"),
]

CONF = cfg.CONF
CONF.register_opts(OPTS)
