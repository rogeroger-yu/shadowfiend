# -*- coding: utf-8 -*-
# Copyright 2014 Objectif Libre
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
from shadowfiend.db import api as dbapi
from shadowfiend.db import models as db_models


LOG = log.getLogger(__name__)


class Handler(object):

    dbapi = dbapi.get_instance()

    def __init__(self):
        super(Handler, self).__init__()

    def create_order(cls, context, **kwargs):
        LOG.debug('create order: Received message from RPC.')
        order = db_models.Order(**kwargs)
        return cls.dbapi.create_order(context, order)

    def close_order(cls, context, **kwargs):
        LOG.debug('close order: Received message from RPC.')
        return cls.dbapi.close_order(context, kwargs['order_id'])

    def get_order(cls, context, **kwargs):
        LOG.debug('get order: Received message from RPC.')
        return cls.dbapi.get_order(context, kwargs['order_id'])

    def get_order_by_resource_id(cls, context, **kwargs):
        LOG.debug('get order by resource id: Received message from RPC.')
        return cls.dbapi.get_order_by_resource_id(
            context, kwargs['resource_id'])

    def update_order(cls, context, **kwargs):
        LOG.debug('update order: Received message from RPC.')
        return cls.dbapi.update_order(
            context, **kwargs)
