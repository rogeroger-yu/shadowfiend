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

import logging

from shadowfiend.client import client


LOG = logging.getLogger(__name__)
TIMESTAMP_TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


class Client(object):
    """Client for shadowfiend v1 API

    """
    def __init__(self, auth_plugin="token",
                 verify=True, cert=None, timeout=None, *args, **kwargs):
        self.client = client.Client(auth_plugin=auth_plugin,
                                    verify=verify,
                                    cert=cert,
                                    timeout=timeout,
                                    *args, **kwargs)

    def get_billing_owner(self, project_id):
        resp, body = self.client.get('/projects/%s/billing_owner' %
                                     project_id)
        return body

    def create_project(self, user_id, project_id, domain_id, consumption):
        _body = dict(user_id=user_id,
                     project_id=project_id,
                     domain_id=domain_id,
                     consumption=consumption)
        self.client.post('/projects', body=_body)

    def get_project(self, project_id):
        resp, body = self.client.get('/projects/%s' % project_id)
        return body

    def get_projects(self, user_id=None, type=None, duration=None):
        _body = dict(user_id=user_id,
                     type=type,
                     duration=duration)
        resp, body = self.client.get('/projects', body=_body)
        return body

    def get_account(self, user_id):
        resp, body = self.client.get('/accounts/%s' % user_id)
        return body

    def get_accounts(self, owed=None, limit=None, offset=None, duration=None):
        _body = dict(owed=owed,
                     limit=limit,
                     offset=offset,
                     duration=duration)
        resp, body = self.client.get('/accounts', body=_body)
        return body

    def create_account(self, user_id, domain_id, balance,
                       consumption, level, **kwargs):
        _body = dict(user_id=user_id,
                     domain_id=domain_id,
                     balance=balance,
                     consumption=consumption,
                     level=level,
                     **kwargs)
        self.client.post('/accounts', body=_body)

    def delete_account(self, user_id):
        resp, body = self.client.delete('/accounts/%s' % user_id)
        return body

    def change_account_level(self, user_id, level):
        _body = dict(level=level)
        self.client.put('/accounts/%s/level' % user_id, body=_body)

    def update_account(self, **kwargs):
        user_id = kwargs.pop('user_id')
        self.client.put('/accounts/%s' % user_id, body=kwargs)

    def get_charges(self, user_id):
        resp, body = self.client.get('/accounts/%s/charges' % user_id)
        if body:
            return body['charges']
        return []

    def get_order(self, order_id):
        resp, body = self.client.get('/orders/%s' % order_id)
        return body

    def get_orders(self, status=None, project_id=None, owed=None,
                   region_id=None, type=None, bill_methods=None):
        params = dict(status=status,
                      type=type,
                      project_id=project_id,
                      owed=owed,
                      region_id=region_id,
                      bill_methods=bill_methods)
        resp, body = self.client.get('/orders', params=params)
        if body:
            return body['orders']
        return []

    def create_order(self, order_id, region_id, unit_price,
                     unit, **kwargs):
        _body = dict(order_id=order_id,
                     region_id=region_id,
                     unit_price=unit_price,
                     unit=unit,
                     **kwargs)
        self.client.post('/orders', body=_body)

    def update_order(self, order_id, change_to, cron_time=None,
                     change_order_status=True, first_change_to=None):
        _body = dict(order_id=order_id,
                     change_to=change_to,
                     cron_time=cron_time,
                     change_order_status=change_order_status,
                     first_change_to=first_change_to)
        self.client.put('/orders', body=_body)
        return True, None

    def close_order(self, order_id):
        self.client.put('/orders/%s/close' % order_id)

    def delete_resource_order(self, order_id, resource_type):
        _body = dict(resource_type=resource_type)
        resp, body = self.client.post('/orders/%s/delete_resource' % order_id,
                                      body=_body)
        if body:
            return body
        return {}

    def get_active_orders(self, user_id=None, project_id=None, owed=None,
                          charged=None, region_id=None, bill_methods=None):
        params = dict(user_id=user_id,
                      project_id=project_id,
                      owed=owed,
                      charged=charged,
                      region_id=region_id,
                      bill_methods=bill_methods)
        resp, body = self.client.get('/orders/active', params=params)
        if body:
            return body
        return []

    def get_active_order_count(self, region_id=None, owed=None, type=None,
                               bill_methods=None):
        params = dict(region_id=region_id,
                      owed=owed,
                      type=type,
                      bill_methods=bill_methods)
        resp, body = self.client.get('/orders/count',
                                     params=params)
        return body

    def get_stopped_order_count(self, region_id=None, owed=None, type=None,
                                bill_methods=None):
        params = dict(region_id=region_id,
                      owed=owed,
                      type=type,
                      bill_methods=bill_methods)
        resp, body = self.client.get('/orders/stopped',
                                     params=params)
        return body
