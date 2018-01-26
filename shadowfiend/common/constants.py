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

# Order and resource State
STATE_RUNNING = 'running'
STATE_STOPPED = 'stopped'
STATE_STOPPED_IN_30_DAYS = 'stopped_in_30_days'
STATE_DELETED = 'deleted'
STATE_SUSPEND = 'suspend'
STATE_CHANGING = 'changing'
STATE_ERROR = 'error'


# Service type
SERVICE_COMPUTE = 'compute'
SERVICE_BLOCKSTORAGE = 'block_storage'
SERVICE_NETWORK = 'network'


# Resource type
RESOURCE_INSTANCE = 'instance'
RESOURCE_IMAGE = 'image'
RESOURCE_SNAPSHOT = 'snapshot'
RESOURCE_VOLUME = 'volume'
RESOURCE_FLOATINGIP = 'floatingip'
RESOURCE_GWRATELIMIT = 'gwratelimit'
RESOURCE_FIPRATELIMIT = 'fipratelimit'
RESOURCE_LOADBALANCER = 'loadbalancer'
RESOURCE_USER = 'user'
RESOURCE_PROJECT = 'project'


ORDER_TYPE = []
