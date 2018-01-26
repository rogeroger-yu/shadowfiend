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

import logging as log
import time

from neutronclient.common import exceptions
from neutronclient.v2_0 import client as neutron_client
from oslo_config import cfg

from shadowfiend.common import constants as const
from shadowfiend.common import timeutils
from shadowfiend.common import utils
from shadowfiend.services import BaseClient
from shadowfiend.services import Resource

LOG = log.getLogger(__name__)

OPTS = [
    cfg.BoolOpt('reserve_fip',
                default=True,
                help="Reserve floating ip or not when account owed")
]
cfg.CONF.register_opts(OPTS)


FIPSET_IS_AVAILABLE = None


def drop_resource(service, resource_id):
    _neutron_client = NeutronClient()
    if service == 'ratelimit.fip':
        _neutron_client.delete_fip(resource_id)
    elif service == 'loadbalancer':
        _neutron_client.delete_loadbalancer(resource_id)


class NeutronClient(BaseClient):
    def __init__(self):
        super(NeutronClient, self).__init__()

        self.neutron_client = neutron_client.Client(
            session=self.session,
            auth=self.auth)

    def subnet_list(self, project_id, region_name=None):
        subnets = self.neutron_client.list_subnets(
            tenant_id=project_id).get('subnets')
        return subnets

    def loadbalancer_list(self, project_id,
                          region_name=None, project_name=None):
        lbs = self.neutron_client.list_loadbalancers(
            tenant_id=project_id).get('loadbalancers')
        formatted_loadbalancer = []
        for lb in lbs:
            formatted_loadbalancer.append(
                Loadbalancer(id=lb['id'],
                             name=lb['name'],
                             is_bill=False,
                             resource_type=const.RESOURCE_LOADBALANCER,
                             tenant_id=lb['tenant_id']))

        return formatted_loadbalancer

    def loadbalancer_get(self, lb_id, region_name=None):
        return self.neutron_client.show_loadbalancer(lb_id)['loadbalancer']

    def pool_list(self, project_id, region_name=None):
        pools = self.neutron_client.list_lbaas_pools(
            tenant_id=project_id).get('pools')
        return pools

    def network_list(self, project_id, region_name=None, project_name=None):
        networks = self.neutron_client.list_networks(
            tenant_id=project_id).get('networks')
        formatted_networks = []
        for network in networks:
            status = utils.transform_status(network['status'])
            formatted_networks.append(
                Network(id=network['id'],
                        name=network['name'],
                        is_bill=False,
                        resource_type='network',
                        status=status,
                        project_id=network['tenant_id'],
                        project_name=project_name,
                        original_status=network['status']))
        return formatted_networks

    def floatingip_get(self, fip_id, region_name=None):
        try:
            fip = self.neutron_client.show_floatingip(fip_id).get('floatingip')
        except exceptions.NotFound:
            return None
        except exceptions.NeutronException as e:
            if e.status_code == 404:
                return None
            raise e
        status = utils.transform_status(fip['status'])
        return FloatingIp(id=fip['id'],
                          name=fip['uos:name'],
                          providers=fip['uos:service_provider'],
                          resource_type=const.RESOURCE_FLOATINGIP,
                          status=status,
                          original_status=fip['status'],
                          is_reserved=True)

    def router_get(self, router_id, region_name=None):
        try:
            router = self.neutron_client.show_router(router_id).get('router')
        except exceptions.NotFound:
            return None
        except exceptions.NeutronException as e:
            if e.status_code == 404:
                return None
            raise e
        status = utils.transform_status(router['status'])
        return Router(id=router['id'],
                      name=router['name'],
                      resource_type=const.RESOURCE_ROUTER,
                      status=status,
                      original_status=router['status'])

    def floatingip_list(self, project_id, region_name=None, project_name=None):
        if project_id:
            fips = self.neutron_client.list_floatingips(
                tenant_id=project_id).get('floatingips')
        else:
            fips = self.neutron_client.list_floatingips().get('floatingips')
        formatted_fips = []
        for fip in fips:
            created_at = utils.format_datetime(fip['created_at'])
            status = utils.transform_status(fip['status'])
            is_bill = False if fip.get('floatingipset_id') else True
            formatted_fips.append(
                FloatingIp(id=fip['id'],
                           name=fip['uos:name'],
                           is_bill=is_bill,
                           size=fip['rate_limit'],
                           providers=fip['uos:service_provider'],
                           project_id=fip['tenant_id'],
                           project_name=project_name,
                           resource_type=const.RESOURCE_FLOATINGIP,
                           status=status,
                           original_status=fip['status'],
                           created_at=created_at))

        return formatted_fips

    def delete_fips(self, project_id, region_name=None):

        # Get floating ips
        fips = self.neutron_client.list_floatingips(tenant_id=project_id)
        fips = fips.get('floatingips')

        # Disassociate these floating ips
        update_dict = {'port_id': None}
        for fip in fips:
            try:
                self.neutron_client.update_floatingip(
                    fip['id'],
                    {'floatingip': update_dict})
            except Exception:
                pass

        # Release these floating ips
        for fip in fips:
            try:
                self.neutron_client.delete_floatingip(fip['id'])
                LOG.warn("Delete floatingip: %s" % fip['id'])
            except Exception:
                pass

    def delete_networks(self, project_id, region_name=None):
        from shadowfiend.services import nova
        nova_client = nova.get_novaclient(region_name)

        # delete all ports
        ports = self.neutron_client.list_ports(
            tenant_id=project_id).get('ports')
        for port in ports:
            try:
                if port['device_owner'] == 'network:router_interface':
                    body = dict(subnet_id=port['fixed_ips'][0]['subnet_id'])
                    self.neutron_client.remove_interface_router(
                        port['device_id'], body)
                elif port['device_owner'] == 'compute:None':
                    nova_client.servers.interface_detach(
                        port['device_id'], port['id'])
                    time.sleep(1)  # wait a second to detach interface
                    try:
                        self.neutron_client.delete_port(port['id'])
                    except Exception:
                        time.sleep(1)
                        self.neutron_client.delete_port(port['id'])
                elif port['device_owner'] == '':
                    self.neutron_client.delete_port(port['id'])
            except Exception:
                pass

        # delete all subnets
        subnets = self.neutron_client.list_subnets(
            tenant_id=project_id).get('subnets')
        for subnet in subnets:
            try:
                self.neutron_client.delete_subnet(subnet['id'])
            except Exception:
                pass

        # delete all networks
        networks = self.neutron_client.list_networks(
            tenant_id=project_id).get('networks')
        for network in networks:
            try:
                self.neutron_client.delete_network(network['id'])
            except Exception:
                pass

    def delete_loadbalancer(self, id, region_name=None):
        self.neutron_client.delete_loadbalancer(id)

    def delete_loadbalancers(self, project_id, region_name=None):
        loadbalancers = self.neutron_client.list_loadbalancers(
            tenant_id=project_id).get('loadbalancers')

        # delete the listeners first
        self.delete_listeners(project_id, region_name)

        for loadbalancer in loadbalancers:
            self.neutron_client.delete_loadbalancer(loadbalancer['id'])
            LOG.warn("Delete loadbalancer: %s" % loadbalancer['id'])

    def delete_fip(self, fip_id, region_name=None):
        update_dict = {'port_id': None}
        self.neutron_client.update_floatingip(fip_id,
                                              {'floatingip': update_dict})
        self.neutron_client.delete_floatingip(fip_id)

    def stop_fip(self, fip_id, region_name=None):
        try:
            fip = self.neutron_client.show_floatingip(fip_id).get('floatingip')
        except exceptions.NotFound:
            return False
        except exceptions.NeutronException as e:
            if e.status_code == 404:
                return False

        if cfg.CONF.reserve_fip:
            return True

        if fip and fip['uos:registerno']:
            return True

        update_dict = {'port_id': None}
        self.neutron_client.update_floatingip(fip_id,
                                              {'floatingip': update_dict})
        self.neutron_client.delete_floatingip(fip_id)
        return False


class FloatingIp(Resource):

    def to_message(self):
        msg = {
            'event_type': 'floatingip.create.end.again',
            'payload': {
                'floatingip': {
                    'id': self.id,
                    'uos:name': self.name,
                    'uos:service_provider': self.providers,
                    'rate_limit': self.size,
                    'tenant_id': self.project_id
                }
            },
            'timestamp': utils.format_datetime(timeutils.strtime())
        }
        return msg

    def to_env(self):
        """fack http env variables for use product items.

        :returns: env(dict)

        """
        return dict(HTTP_X_USER_ID=None, HTTP_X_PROJECT_ID=self.project_id)

    def to_body(self):
        """fack http body.

        :returns: body(dict)

        """
        body = {}
        body[self.resource_type] = dict(rate_limit=self.size)
        return body


class FloatingIpSet(Resource):
    def to_message(self):
        msg = {
            'event_type': 'floatingipset.create.end.again',
            'payload': {
                'floatingipset': {
                    'id': self.id,
                    'uos:name': self.name,
                    'uos:service_provider': self.providers,
                    'rate_limit': self.size,
                    'tenant_id': self.project_id
                }
            },
            'timestamp': utils.format_datetime(timeutils.strtime())
        }
        return msg


class Router(Resource):
    def to_message(self):
        msg = {
            'event_type': 'router.create.end.again',
            'payload': {
                'router': {
                    'id': self.id,
                    'name': self.name,
                    'tenant_id': self.project_id
                }
            },
            'timestamp': utils.format_datetime(timeutils.strtime())
        }
        return msg

    def to_env(self):
        return dict(HTTP_X_USER_ID=None, HTTP_X_PROJECT_ID=self.project_id)

    def to_body(self):
        return {}


class Listener(Resource):
    def to_message(self):
        msg = {
            'event_type': 'listener.create.end',
            'payload': {
                'listener': {
                    'id': self.id,
                    'name': self.name,
                    'admin_state_up': self.admin_state_up,
                    'connection_limit': self.connection_limit,
                    'tenant_id': self.project_id
                }
            },
            'timestamp': utils.format_datetime(timeutils.strtime())
        }
        return msg

    def to_env(self):
        return dict(HTTP_X_USER_ID=None, HTTP_X_PROJECT_ID=self.project_id)

    def to_body(self):
        body = {}
        body[self.resource_type] = dict(connection_limit=self.connection_limit)
        return body


class Loadbalancer(Resource):
        pass


class Network(Resource):
        pass
