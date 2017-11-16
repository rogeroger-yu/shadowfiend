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

from oslo_log import log

from shadowfiend.client import client
from shadowfiend import utils as gringutils


LOG = log.getLogger(__name__)
TIMESTAMP_TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

quantize_decimal = gringutils._quantize_decimal


class Client(object):
    """Client for shadowfiend noauth API

    """
    def __init__(self, auth_plugin="noauth",
                 verify=True, cert=None, timeout=None, *args, **kwargs):
        self.client = client.Client(auth_plugin=auth_plugin,
                                    verify=verify,
                                    cert=cert,
                                    timeout=timeout,
                                    *args, **kwargs)

    def create_account(self, user_id, domain_id,
                       balance, consumption, level, **kwargs):
        _body = dict(user_id=user_id,
                     domain_id=domain_id,
                     balance=balance,
                     consumption=consumption,
                     level=level,
                     **kwargs)
        self.client.post('/accounts', body=_body)

    def create_project(self, project_id, domain_id, consumption, user_id=None):
        _body = dict(user_id=user_id,
                     project_id=project_id,
                     domain_id=domain_id,
                     consumption=consumption)
        self.client.post('/projects', body=_body)

    def delete_resources(self, project_id, region_name=None):
        params = dict(project_id=project_id,
                      region_name=region_name)
        self.client.delete('/resources', params=params)

    def change_billing_owner(self, user_id, project_id):
        _body = dict(user_id=user_id)
        self.client.put('/projects/%s/billing_owner' % project_id, body=_body)

    def get_project(self, project_id):
        resp, body = self.client.get('/projects/%s' % project_id)
        return body
