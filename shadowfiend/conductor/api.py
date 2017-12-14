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

"""API for interfacing with shadowfiend Backend."""
from oslo_config import cfg

from shadowfiend.common import service as rpc_service


# The Backend API class serves as a AMQP client for communicating
# on a topic exchange specific to the conductors.  This allows the ReST
# API to trigger operations on the conductors

class API(rpc_service.API):
    def __init__(self, transport=None, context=None, topic=None):
        if topic is None:
            cfg.CONF.import_opt('topic', 'shadowfiend.conductor.config',
                                group='conductor')
        super(API, self).__init__(transport, context,
                                  topic=cfg.CONF.conductor.topic)

    def change_billing_owner(self, project_id, user_id):
        """"Change billing_owner of this project"""
        kwargs = {'project_id': project_id,
                'user_id': user_id}
        return self._call('change_billing_owner', **kwargs)

    def get_billing_owner(self, context, project_id):
        kwargs = {'project_id': project_id}
        return self._call('get_billing_owner', **kwargs)

    def create_account(self, context, account):
        return self._call('create_account', **account)

    def create_project(self, context, project):
        return self._call('create_project', **project)

    def get_project(self, context, project_id):
        kwargs = {'project_id': project_id}
        return self._call('get_project', **kwargs)

    def get_account(self, context, user_id):
        kwargs = {'user_id': user_id}
        return self._call('get_account', **kwargs)
