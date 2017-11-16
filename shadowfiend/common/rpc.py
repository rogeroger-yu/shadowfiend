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

import oslo_messaging as messaging
from oslo_serialization import jsonutils

from shadowfiend.common import context as shadowfiend_context
from shadowfiend.common import exception

ALLOWED_EXMODS = [
    exception.__name__,
]
EXTRA_EXMODS = []

TRANSPORT_ALIASES = {
    'shadowfiend.openstack.common.rpc.impl_kombu': 'rabbit',
    'shadowfiend.openstack.common.rpc.impl_qpid': 'qpid',
    'shadowfiend.openstack.common.rpc.impl_zmq': 'zmq',
    'shadowfiend.rpc.impl_kombu': 'rabbit',
    'shadowfiend.rpc.impl_qpid': 'qpid',
    'shadowfiend.rpc.impl_zmq': 'zmq',
}


class JsonPayloadSerializer(messaging.NoOpSerializer):
    @staticmethod
    def serialize_entity(context, entity):
        return jsonutils.to_primitive(entity, convert_instances=True)


class RequestContextSerializer(messaging.Serializer):

    def __init__(self, base):
        self._base = base

    def serialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.serialize_entity(context, entity)

    def deserialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.deserialize_entity(context, entity)

    def serialize_context(self, context):
        return context.to_dict()

    def deserialize_context(self, context):
        return shadowfiend_context.RequestContext.from_dict(context)


def init(conf):
    global TRANSPORT, NOTIFIER
    exmods = get_allowed_exmods()
    TRANSPORT = messaging.get_transport(conf,
                                        allowed_remote_exmods=exmods,
                                        aliases=TRANSPORT_ALIASES)
    serializer = RequestContextSerializer(JsonPayloadSerializer())
    NOTIFIER = messaging.Notifier(TRANSPORT, serializer=serializer)


def set_defaults(control_exchange):
    messaging.set_transport_defaults(control_exchange)


def get_allowed_exmods():
    return ALLOWED_EXMODS + EXTRA_EXMODS
