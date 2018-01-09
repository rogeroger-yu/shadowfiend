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

import eventlet
import os
import oslo_i18n
import oslo_messaging as messaging
import socket
import sys

from oslo_config import cfg
from oslo_log import log
from oslo_service import service

from shadowfiend.common import config
from shadowfiend.common import rpc
from shadowfiend.objects import base as objects_base

eventlet.monkey_patch()

LOG = log.getLogger(__name__)

TRANSPORT_ALIASES = {
    'shadowfiend.openstack.common.rpc.impl_kombu': 'rabbit',
    'shadowfiend.openstack.common.rpc.impl_qpid': 'qpid',
    'shadowfiend.openstack.common.rpc.impl_zmq': 'zmq',
}

service_opts = [
    cfg.StrOpt('host',
               default=socket.getfqdn(),
               help='Name of this node. This can be an opaque identifier. '
               'It is not necessarily a hostname, FQDN, or IP address. '
               'However, the node name must be valid within an AMQP key, '
               'and if using ZeroMQ, a valid hostname, FQDN, or IP address.'),
    cfg.IntOpt('report_interval',
               default=10,
               help='Seconds between nodes reporting state to datastore'),
    cfg.BoolOpt('periodic_enable',
                default=True,
                help='Enable periodic tasks'),
    cfg.IntOpt('periodic_fuzzy_delay',
               default=60,
               help='Range of seconds to randomly delay when starting the'
                    ' periodic task scheduler to reduce stampeding.'
                    ' (Disable by setting to 0)'),
    cfg.IntOpt('periodic_interval_max',
               default=60,
               help='Max interval size between periodic tasks execution in '
                    'seconds.'),
    cfg.IntOpt('periodic_interval_max',
               default=60,
               help='Max interval size between periodic tasks execution in '
                    'seconds.'),
]

cfg.CONF.register_opts(service_opts)


def prepare_service(argv=None, config_files=None):
    oslo_i18n.enable_lazy()
    log.register_options(cfg.CONF)
    log.set_defaults()
    config.set_middleware_defaults()

    if argv is None:
        argv = sys.argv
    config.parse_args(argv)

    log.setup(cfg.CONF, 'shadowfiend')


class Service(service.Service):
    def __init__(self, host, binary, topic, manager,
                 periodic_enable=None, periodic_fuzzy_delay=None,
                 periodic_interval_max=None):
        super(Service, self).__init__()
        self.host = host
        self.binary = binary
        self.topic = topic
        self.manager = manager
        self.binary = binary
        self.periodic_enable = periodic_enable
        self.periodic_fuzzy_delay = periodic_fuzzy_delay
        self.periodic_interval_max = periodic_interval_max

    def start(self):
        # access_policy = dispatcher.DefaultRPCAccessPolicy
        serializer = rpc.RequestContextSerializer(
            objects_base.ShadowfiendObjectSerializer())
        transport = messaging.get_transport(cfg.CONF,
                                            aliases=TRANSPORT_ALIASES)
        target = messaging.Target(topic=self.topic, server=self.host)
        self._server = messaging.get_rpc_server(transport,
                                                target,
                                                self.manager,
                                                serializer=serializer,
                                                executor='eventlet')

        self._server.start()
        LOG.debug("Creating RPC server for service %s", self.topic)

        # if self.periodic_enable:
        #     if self.periodic_fuzzy_delay:
        #         initial_delay = random.randint(0, self.periodic_fuzzy_delay)
        #     else:
        #         initial_delay = None

        #     self.tg.add_dynamic_timer(self.periodic_tasks,
        #                               initial_delay=initial_delay,
        #                               periodic_interval_max=
        #                               self.periodic_interval_max)

    def stop(self):
        if self._server:
            self._server.stop()
            self._server.wait()
        super(Service, self).stop()

    @classmethod
    def create(cls, host=None, binary=None, topic=None, manager=None,
               periodic_enable=None, periodic_fuzzy_delay=None,
               periodic_interval_max=None):

        if not host:
            host = cfg.CONF.host
        if not binary:
            binary = os.path.basename(sys.argv[0])
        if not topic:
            topic = binary.rpartition('shadowfiend-')[2]
        if not manager:
            manager_cls = ('%s_manager' %
                           binary.rpartition('shadowfiend-')[2])
            manager = cfg.CONF.get(manager_cls, None)
        if periodic_enable is None:
            periodic_enable = cfg.CONF.periodic_enable
        if periodic_fuzzy_delay is None:
            periodic_fuzzy_delay = cfg.CONF.periodic_fuzzy_delay
        if periodic_interval_max is None:
            periodic_interval_max = cfg.CONF.periodic_interval_max

        service_obj = cls(host, binary, topic, manager,
                          periodic_enable=periodic_enable,
                          periodic_fuzzy_delay=periodic_fuzzy_delay,
                          periodic_interval_max=periodic_interval_max)

        return service_obj


_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = service.launch(cfg.CONF, server, workers=workers)


def wait():
    _launcher.wait()


class API(object):
    def __init__(self, transport=None, context=None, topic=None, server=None,
                 timeout=None):
        serializer = rpc.RequestContextSerializer(
            objects_base.ShadowfiendObjectSerializer())
        if transport is None:
            exmods = rpc.get_allowed_exmods()
            transport = messaging.get_transport(cfg.CONF,
                                                allowed_remote_exmods=exmods,
                                                aliases=TRANSPORT_ALIASES)
        self._context = context
        if topic is None:
            topic = ''
        target = messaging.Target(topic=topic, server=server)
        self._client = messaging.RPCClient(transport, target,
                                           serializer=serializer,
                                           timeout=timeout)

    def _call(self, method, *args, **kwargs):
        return self._client.call(self._context, method, *args, **kwargs)

    def _cast(self, method, *args, **kwargs):
        self._client.cast(self._context, method, *args, **kwargs)

    def echo(self, message):
        self._cast('echo', message=message)
