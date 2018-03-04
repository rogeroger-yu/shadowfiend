# -*- coding: utf-8 -*-
# Copyright 2014 Objectif Libre
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

from keystoneauth1 import loading as ks_loading
from neutronclient.v2_0 import client as neutron_client

from oslo_config import cfg
from oslo_log import log

LOG = log.getLogger(__name__)
CONF = cfg.CONF


def drop_resource(service, resource_id):
    _neutron_client = NeutronClient()
    if service == 'ratelimit.fip':
        _neutron_client.delete_fip(resource_id)
    elif service == 'loadbalancer':
        _neutron_client.delete_loadbalancer(resource_id)


class NeutronClient(object):
    def __init__(self):
        ks_loading.register_session_conf_options(CONF, "neutron_client")
        ks_loading.register_auth_conf_options(CONF, "neutron_client")
        self.auth = ks_loading.load_auth_from_conf_options(
            CONF,
            "neutron_client")
        self.session = ks_loading.load_session_from_conf_options(
            CONF,
            "neutron_client",
            auth=self.auth)
        self.neutron_client = neutron_client.Client(
            session=self.session,
            auth=self.auth)

    def delete_loadbalancer(self, id, region_name=None):
        self.neutron_client.delete_loadbalancer(id)

    def delete_fip(self, fip_id, region_name=None):
        update_dict = {'port_id': None}
        self.neutron_client.update_floatingip(fip_id,
                                              {'floatingip': update_dict})
        self.neutron_client.delete_floatingip(fip_id)
