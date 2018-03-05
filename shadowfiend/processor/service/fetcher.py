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

import copy
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


LOG = log.getLogger(__name__)
CONF = cfg.CONF

SHADOWFIEND_STATE_RESOURCE = 'shadowfiend_state'
SHADOWFIEND_STATE_METRIC = 'state'

resource_mappings = {
    'compute': 'instance',
    'image': 'image',
    'volume.volume': 'volume',
    'volume.snapshot': 'volume',
    'loadbalancer': 'network_lbaas_loadbalancer',
    'ratelimit.fip': 'ratelimit',
    'ratelimit.gw': 'ratelimit',
}

metric_mappings = {
    'volume.volume': 'volume.size',
    'volume.snapshot': 'volume.snapshot.size',
    'ratelimit.fip': 'ratelimit.fip',
    'ratelimit.gw': 'ratelimit.gw',
}

START_TIME = timeutils.str2ts("2010-01-01T00:00:00Z")


class KeystoneFetcher(KeystoneClient):
    def __init__(self):
        super(KeystoneFetcher, self).__init__()

    def get_rate_projects(self):
        keystone_version = discover.normalize_version_number('3')
        auth_dispatch = {(3,): ('project', 'projects', 'list'),
                         (2,): ('tenant', 'tenants', 'roles_for_user')}
        for auth_version, auth_version_mapping in six.iteritems(auth_dispatch):
            if discover.version_match(auth_version, keystone_version):
                return self._do_get_projects(auth_version_mapping)
        msg = "Keystone version you've specified is not supported"
        raise exceptions.VersionNotAvailable(msg)

    def _do_get_projects(self, auth_version_mapping):
        # project_attr: project,project_attrs: projects,role_func: list
        project_attr, projects_attr, role_func = auth_version_mapping
        project_list = getattr(self.ks_client, projects_attr).list()
        user_list = getattr(self.ks_client.users, 'list')(
            **{project_attr: project_list[0]})
        for user in user_list:
            if user.__dict__['name'] == 'cloudkitty':
                rating_user = user.id
                break
        for project in project_list[:]:
            roles = getattr(self.ks_client.roles, role_func)(
                **{'user': rating_user,
                   project_attr: project})
            if 'rating' not in [role.name for role in roles]:
                project_list.remove(project)
        return [project.id for project in project_list]

    def get_rate_user(self, project_id):
        role_id = getattr(self.ks_client.roles, 'list')(
            **{'name': 'billing_owner',
               'project': project_id})[0].id
        role_assign = getattr(self.ks_client.role_assignments, 'list')(
            **{'role': role_id,
               'project': project_id})

        return (role_assign[0].user['id'] if role_assign != [] else
                role_assign)

    def get_users(self):
        user_list = getattr(self.ks_client, 'users').list()
        return [user.id for user in user_list]


class GnocchiFetcher(GnocchiClient):
    def __init__(self):
        super(GnocchiFetcher, self).__init__()
        self._period = CONF.processor.cloudkitty_period

    def set_state(self, project_id, state):
        query = {"=": {"project_id": project_id}}
        # get resource_id, if not, create it
        resources = self.gnocchi_client.resource.search(
            resource_type=SHADOWFIEND_STATE_RESOURCE,
            query=query,
            limit=1)
        if not resources:
            # NOTE(sheeprine): We don't have the user id information and we are
            # doing rating on a per project basis. Put garbage in it
            resource = self.gnocchi_client.resource.create(
                resource_type=SHADOWFIEND_STATE_RESOURCE,
                resource={'id': uuid.uuid4(),
                          'user_id': None,
                          'project_id': project_id})
            resource_id = resource['id']
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
            [{'timestamp': timeutils.ts2dt(state).isoformat(),
             'value': 1}])

    def get_state(self, project_id, state_type, order_type):
        query = {"=": {"project_id": project_id}}
        resources = self.gnocchi_client.resource.search(
            resource_type=('%s_state' % state_type),
            query=query,
            limit=1)

        if not resources:
            # NOTE(sheeprine): We don't have the user id information and we are
            # doing rating on a per project basis. Put garbage in it
            LOG.warning("There is no %s state resource" % state_type)
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

    def get_current_consume(self, project_id, start_stamp=None):
        if not start_stamp:
            _stamp = self.get_state(project_id, 'shadowfiend', 'top')
            start_stamp = (_stamp if _stamp is not None else
                           self.get_state(project_id, 'cloudkitty', 'bottom'))
        query = {"=": {"project_id": project_id}}

        def aggregate(start_stamp, period, query, granularity):
            return self.gnocchi_client.metric.aggregation(
                start=start_stamp,
                stop=((start_stamp + period) if start_stamp is not None
                      else None),
                query=query,
                metrics='total.cost',
                aggregation='sum',
                granularity=granularity)
        try:
            current_consume = aggregate(
                start_stamp, self._period, query, self._period)
        except Exception:
            current_consume = aggregate(
                start_stamp, self._period, query, 86400)
        return current_consume[0][2] if current_consume != [] else 0

    def get_resource_price(self, metric_id, start=None, stop=None,
                           aggregation='sum', granularity=None):
        _granularity = granularity or self._period
        measures = self.gnocchi_client.metric.get_measures(
            metric=metric_id,
            start=start,
            stop=stop,
            aggregation=aggregation,
            granularity=_granularity,
            refresh=True)
        total_price = 0
        for measure in measures:
            total_price += measure[2] if measure[1] == _granularity else 0
        return total_price

    def get_resources(self, project_id, service):
        query = ({"=": {"project_id": project_id}} if project_id else
                 {">=": {"started_at": "2010-01-01"}})
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

    def get_summary(self, project_id=None):
        query = ({"and": [{"=": {"project_id": project_id}}]}
                 if project_id else {">=": {"started_at": "2010-01-01"}})
        start_at = START_TIME
        end_at = None
        try:
            def _aggregate(resource_type, query, start_at, end_at):
                return self.gnocchi_client.metric.aggregation(
                    resource_type=resource_type,
                    query=query,
                    start=start_at,
                    stop=end_at,
                    metrics='total.cost',
                    aggregation='sum',
                    granularity=86400,
                    needed_overlap=0)

            def _add_up(orders):
                total_price = 0
                for order in orders:
                    total_price += order[2]
                return round(total_price, 4)

            total_consumption = []

            for _service in CONF.processor.services:
                orders = _aggregate(resource_type=resource_mappings[_service],
                                    query=query, start_at=start_at,
                                    end_at=end_at)
                total_consumption.append({'total_price': _add_up(orders),
                                          'type': _service})

            _generic = _aggregate(resource_type='generic',
                                  query=query,
                                  start_at=start_at,
                                  end_at=end_at)
            total_consumption.append({'total_price': _add_up(_generic),
                                      'type': 'generic'})
            return total_consumption
        except Exception as e:
            LOG.error("Error resion : %s" % e)

    def get_bills(self, resource_type, project_id=None,
                  limit=None, marker=None):
        query = ({"and": [{"=": {"project_id": project_id}}]}
                 if project_id else {">=": {"started_at": "2010-01-01"}})

        def _add_up(orders):
            total_price = 0
            for order in orders:
                total_price += order[2]
            return round(total_price, 4)

        def _pagination(resources, limit, marker=None):
            result = []
            start_index = None
            _marker = marker
            if len(resources) <= limit:
                return (resources, False, marker)
            for index, resource in enumerate(resources):
                if len(result) < limit and resource:
                    if resource['id'] == _marker or not _marker:
                        start_index = index + 1
                        _marker = 1
                    if index == start_index:
                        result.append(resource)
                        start_index += 1
                else:
                    return ((result, True, resources[index - 1]['id']) if
                            resource else (result, False, marker))

        resources = self.gnocchi_client.resource.search(
            resource_type=resource_mappings[resource_type],
            query=query)

        if resources == []:
            return {"total_count": 0, "orders": [], "links": {}}

        for resource in resources[:]:
            mappings = copy.copy(resource_mappings)
            if mappings.pop(resource_type) in mappings.values():
                orders = self.gnocchi_client.metric.get_measures(
                    metric_mappings[resource_type], resource_id=resource['id'])
                if orders == []:
                    resources.remove(resource)
                    continue
            try:
                orders = self.gnocchi_client.metric.get_measures(
                    'total.cost',
                    resource_id=resource['id'],
                    granularity=self._period,
                    aggregation='sum')
                resource.update({'total_price': _add_up(orders)})
            except Exception as e:
                LOG.error("Error resion: %s, the resource id is % s" %
                          (e, resource['id']))
                resource.update({'total_price': 0})
        result = (_pagination(resources, limit, marker) if limit
                  else (resources, None))

        return ({"total_count": len(resources),
                 "orders": result[0],
                 "links": {"next": result[1], "marker": result[2]}})
