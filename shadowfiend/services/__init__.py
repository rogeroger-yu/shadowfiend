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

from shadowfiend.client.v1 import client

from oslo_config import cfg
from oslo_log import log

from keystoneauth1 import loading as ks_loading
from keystoneauth1 import session as ks_session 


LOG = log.getLogger(__name__)
CONF = cfg.CONF

SERVICE_CLIENT_OPTS = 'service_client'


class BaseClient(object):
    def __init__(self):
        ks_loading.register_session_conf_options(CONF, SERVICE_CLIENT_OPTS)
        ks_loading.register_auth_conf_options(CONF, SERVICE_CLIENT_OPTS)

        self.auth = ks_loading.load_auth_from_conf_options(CONF, SERVICE_CLIENT_OPTS)
        self.session = ks_loading.load_session_from_conf_options(CONF, SERVICE_CLIENT_OPTS, auth=self.auth)
