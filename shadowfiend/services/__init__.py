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

import functools

from decimal import Decimal
from oslo_config import cfg
from oslo_log import log

from keystoneauth1 import loading as ks_loading

from shadowfiend.client.v1 import client
from shadowfiend.common.exception import ShadowfiendException


LOG = log.getLogger(__name__)
CONF = cfg.CONF

SERVICE_CLIENT_OPTS = 'service_client'


class BaseClient(object):
    def __init__(self):
        ks_loading.register_session_conf_options(CONF, SERVICE_CLIENT_OPTS)
        ks_loading.register_auth_conf_options(CONF, SERVICE_CLIENT_OPTS)
        self.auth = ks_loading.load_auth_from_conf_options(
            CONF,
            SERVICE_CLIENT_OPTS)
        self.session = ks_loading.load_session_from_conf_options(
            CONF,
            SERVICE_CLIENT_OPTS,
            auth=self.auth)


class Resource(object):
    def __init__(self, id, name, resource_type, is_bill=True,
                 status=None, original_status=None, **kwargs):
        self.id = id
        self.name = name
        self.resource_type = resource_type
        self.is_bill = is_bill
        self.status = status
        self.original_status = original_status

        self.fields = list(kwargs)
        self.fields.extend(['id', 'name', 'resource_type', 'is_bill',
                            'status', 'original_status'])

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def as_dict(self):
        d = {}
        for f in self.fields:
            v = getattr(self, f)
            d[f] = v
        return d

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self):
        return '%s: %s: %s' % (self.resource_type, self.name, self.id)

    def __eq__(self, other):
        return (self.id == other.id and
                self.original_status == other.original_status)


def wrap_exception(exc_type=None, with_raise=False):
    """Wrap exception around resource method

    This decorator wraps a method to catch any exceptions that may get thrown.
    It logs the exception, and may sends message to notification system.

    In every normal situation, there will not exception be raised.
    When it requests a non-exists resource, it will return None instead of
    exception. Only when any of the services is not avaliable,
    it will raise an exception to stop the further execution.
    """

    def inner(f):
        def wrapped(uuid, *args, **kwargs):
            try:
                if exc_type == 'delete' or exc_type == 'stop':
                    gclient = client.get_client()
                    order = gclient.get_order_by_resource_id(uuid)
                    account = gclient.get_account(order['user_id'])
                    if (order['unit'] == 'hour' and
                        order['owed'] and
                        account['owed'] and
                        Decimal(str(account['balance'])) < 0 and
                        int(account['level']) != 9) or (
                        order['unit'] in ['month', 'year'] and
                        order['owed']):
                        LOG.warn("The resource: %s is indeed owed, can be"
                                 "execute the action: %s", uuid, f.__name__)
                        return f(uuid, *args, **kwargs)
                    else:
                        LOG.warn("The resource: %s is not owed, should not"
                                 "execute the action: %s", uuid, f.__name__)
                else:
                    return f(uuid, *args, **kwargs)
            except Exception as e:
                msg = None
                if (exc_type == 'single' or exc_type == 'delete' or
                        (exc_type == 'stop')):
                    msg = ('Fail to do %s for resource: %s, reason: %s' %
                           (f.__name__, uuid, e))
                elif exc_type == 'bulk':
                    msg = ('Fail to do %s for account: %s, reason: %s' %
                           (f.__name__, uuid, e))
                elif exc_type == 'list':
                    msg = ('Fail to do %s for account: %s, reason: %s' %
                           (f.__name__, uuid, e))
                elif exc_type == 'get':
                    msg = ('Fail to do %s for resource: %s, reason: %s' %
                           (f.__name__, uuid, e))
                elif exc_type == 'put':
                    msg = ('Fail to do %s for resource: %s, reason: %s' %
                           (f.__name__, uuid, e))
                else:
                    msg = ('Fail to do %s, reason: %s' %
                           (f.__name__, e))
                if with_raise:
                    raise ShadowfiendException(message=msg)
                else:
                    LOG.error(msg)
                    return []
        return functools.wraps(f)(wrapped)
    return inner
