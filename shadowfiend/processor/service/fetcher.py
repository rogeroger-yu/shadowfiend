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


import six
import uuid

from dateutil import parser

from oslo_config import cfg
from oslo_log import log

from keystoneclient import discover
from keystoneclient import exceptions

from gnocchiclient import exceptions as gexceptions

from shadowfiend.common import timeutils
from shadowfiend.services.gnocchi import GnocchiClient
from shadowfiend.services.keystone import KeystoneClient
# services test fetcher
# from shadowfiend.services.cinder import CinderClient
# from shadowfiend.services.nova import NovaClient
# from shadowfiend.services.glance import GlanceClient
from shadowfiend.services.neutron import NeutronClient


LOG = log.getLogger(__name__)
CONF = cfg.CONF

SERVICE_CLIENT_OPTS = 'service_client'
SHADOWFIEND_STATE_RESOURCE = 'shadowfiend_state'
SHADOWFIEND_STATE_METRIC = 'state'


class KeystoneFetcher(KeystoneClient):
    def __init__(self):
        super(KeystoneFetcher, self).__init__()

    def get_rate_tenants(self):
        keystone_version = discover.normalize_version_number('3')
        auth_dispatch = {(3,): ('project', 'projects', 'list'),
                         (2,): ('tenant', 'tenants', 'roles_for_user')}
        for auth_version, auth_version_mapping in six.iteritems(auth_dispatch):
            if discover.version_match(auth_version, keystone_version):
                return self._do_get_tenants(auth_version_mapping)
        msg = "Keystone version you've specified is not supported"
        raise exceptions.VersionNotAvailable(msg)

    def _do_get_tenants(self, auth_version_mapping):
        # tenant_attr: project,tenant_attrs: projects,role_func: list
        tenant_attr, tenants_attr, role_func = auth_version_mapping
        tenant_list = getattr(self.ks_client, tenants_attr).list()
        user_list = getattr(self.ks_client.users, 'list')(
            **{tenant_attr: tenant_list[0]})
        for user in user_list:
            if user.__dict__['name'] == 'cloudkitty':
                rating_user = user.id
                break
        for tenant in tenant_list[:]:
            roles = getattr(self.ks_client.roles, role_func)(
                **{'user': rating_user,
                   tenant_attr: tenant})
            if 'rating' not in [role.name for role in roles]:
                tenant_list.remove(tenant)
        return [tenant.id for tenant in tenant_list]

    def get_rate_user(self, tenant_id):
        role_id = getattr(self.ks_client.roles, 'list')(
            **{'name': 'billing_owner',
               'project': tenant_id})[0].id
        role_assign = getattr(self.ks_client.role_assignments, 'list')(
            **{'role': role_id,
               'project': tenant_id})
        return (role_assign[0].user['id'] if role_assign != [] else
                role_assign)

    def get_users(self):
        user_list = getattr(self.ks_client, 'users').list()
        return [user.id for user in user_list]


class GnocchiFetcher(GnocchiClient):
    def __init__(self):
        super(GnocchiFetcher, self).__init__()
        self._period = CONF.processor.cloudkitty_period

    def set_state(self, tenant_id, state):
        query = {"=": {"project_id": tenant_id}}
        # get resource_id, if not, create it
        resources = self.gnocchi_client.resource.search(
            resource_type=SHADOWFIEND_STATE_RESOURCE,
            query=query,
            limit=1)
        if not resources:
            # NOTE(sheeprine): We don't have the user id information and we are
            # doing rating on a per tenant basis. Put garbage in it
            resource = self.gnocchi_client.resource.create(
                resource_type=SHADOWFIEND_STATE_RESOURCE,
                resource={'id': uuid.uuid4(),
                          'user_id': None,
                          'project_id': tenant_id})
            resourcer_id = resource['id']
        else:
            resource_id = resources[0]['id']
        # get metric, if not, create it
        resource = self.gnocchi_client.resource.get(
            resource_type='generic',
            resource_id=resource_id,
            history=False)
        metric_id = resource["metrics"].get(SHADOWFIEND_STATE_METRIC)
        if not metric_id:
            new_metric = {}
            new_metric["archive_policy_name"] = 'billing'
            new_metric["name"] = SHADOWFIEND_STATE_METRIC
            new_metric["resource_id"] = resource_id
            metric = self.gnocchi_client.metric.create(new_metric)
            metric_id = metric['id']
        # set state: add measures to gnocchi
        self.gnocchi_client.metric.add_measures(
            metric_id,
            [{'timestamp': state.isoformat(),
             'value': 1}])

    def get_state(self, tenant_id, state_type, order_type):
        query = {"=": {"project_id": tenant_id}}
        resources = self.gnocchi_client.resource.search(
            resource_type=('%s_state' % state_type),
            query=query,
            limit=1)

        if not resources:
            # NOTE(sheeprine): We don't have the user id information and we are
            # doing rating on a per tenant basis. Put garbage in it
            LOG.warning("There is no % state resource" % state_type)
        else:
            state_resource_id = resources[0]['id']
            try:
                # (aolwas) add "refresh=True" to be sure to get all posted
                # measures for this particular metric
                r = self.gnocchi_client.metric.get_measures(
                    metric='state',
                    resource_id=state_resource_id,
                    query=query,
                    aggregation='sum',
                    limit=1,
                    granularity=self._period,
                    needed_overlap=0,
                    refresh=True)
            except gexceptions.MetricNotFound:
                return
            if len(r) > 0:
                # (aolwas) According http://gnocchi.xyz/rest.html#metrics,
                # gnocchi always returns measures ordered by timestamp
                result = r[-1][0] if order_type == 'top' else r[0][0]
                return timeutils.dt2ts(parser.parse(result))

    def get_current_consume(self, tenant_id, start_stamp=None):
        if not start_stamp:
            _stamp = self.get_state(tenant_id, 'shadowfiend', 'top')
            start_stamp = (_stamp if _stamp is not None else
                           self.get_state(tenant_id, 'cloudkitty', 'bottom'))
        query = {"=": {"project_id": tenant_id}}
        try:
            current_consume = self.gnocchi_client.metric.aggregation(
                start=start_stamp,
                stop=start_stamp + self._period,
                query=query,
                metrics='total.cost',
                aggregation='sum',
                granularity=self._period)
        except gexceptions.NotAcceptable:
            return
        except gexceptions.Unauthorized:
            return
        except Exception:
            LOG.exception('Could not get current consume, Makesure '
                          'your project have correct role relation')
        return current_consume[0][2] if current_consume != [] else 0

    def get_resources(self, tenant_id, service):
        query = {"=": {"project_id": tenant_id}}
        try:
            resources = self.gnocchi_client.resource.search(
                resource_type=service,
                query=query)
        except gexceptions.NotAcceptable:
            return
        except gexceptions.Unauthorized:
            return
        except Exception:
            LOG.exception('Could not get resources')
        return resources


class NeutronFetcher(NeutronClient):
    def __init__(self):
        super(NeutronFetcher, self).__init__()

    def networks_list(self, project_id):
        return self.network_list(project_id)
