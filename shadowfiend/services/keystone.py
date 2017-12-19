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
from oslo_log import log

from keystoneclient import client as ks_client
from shadowfiend.services import BaseClient


LOG = log.getLogger(__name__)
CONF = cfg.CONF

SERVICE_CLIENT_OPTS = 'service_client'


class KeystoneClient(BaseClient):
    def __init__(self):
        super(KeystoneClient, self).__init__()

        self.ks_client = ks_client.Client(
            version='3',
            session=self.session,
            auth_url=self.auth.auth_url)

    def get_role_list(user=None, group=None, domain=None, project=None):
        return self.ks_client.roles.list(user=user,
                                         group=group,
                                         domain=domain,
                                         project=project)

    def get_project_list(doamin=None, name=None, user=None):
        return self.ks_client.projects.list(domain=domain, name=name, user=user)

    def get_domain_list(name=None, enabled=None):
        return self.ks_client.domains.list(name=name, enabled=enabled)

    def get_token():
        return self.ks_client.auth_token

def get_domain_list(name=None, enabled=None):
    ks = KeystoneClient()
    return ks.ks_client.domains.list(name=name, enabled=enabled)

def get_project_list(domain=None, name=None, user=None):
    ks = KeystoneClient()
    return ks.ks_client.projects.list(domain=domain, name=name, user=user)
