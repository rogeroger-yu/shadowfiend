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
# on a topic exchange specific to the processor.  This allows the ReST
# API to trigger operations on the processor

class API(rpc_service.API):
    def __init__(self, transport=None, context=None, topic=None):
        if topic is None:
            cfg.CONF.import_opt('topic', 'shadowfiend.processor.config',
                                group='processor')
        super(API, self).__init__(transport, context,
                                  topic=cfg.CONF.processor.topic)

    def test(self):
        # return 'test RPC'
        # return self._client.cast({}, 'test')
        return self._call('test', arg='test_arg')

#    def cluster_create_async(self, cluster, create_timeout):
#        self._cast('cluster_create', cluster=cluster,
#                   create_timeout=create_timeout)
