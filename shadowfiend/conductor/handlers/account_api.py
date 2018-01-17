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

    def create_account(cls, context, **kwargs):
        LOG.debug('create account: Received message from RPC.')
        account = db_models.Account(**kwargs)
        return cls.dbapi.create_account(context, account)

    def get_account(cls, context, **kwargs):
        LOG.debug('get account: Received message from RPC.')
        account = cls.dbapi.get_account(context, **kwargs)
        return account

    def get_accounts(cls, context, **kwargs):
        LOG.debug('get accounts: Received message from RPC.')
        accounts = cls.dbapi.get_accounts(context, **kwargs)
        return accounts

    def get_accounts_count(cls, context, **kwargs):
        LOG.debug('get accounts count: Received message from RPC.')
        accounts = cls.dbapi.get_accounts_count(context, **kwargs)
        return accounts

    def delete_account(cls, context, **kwargs):
        LOG.debug('delete account: Received message from RPC.')
        cls.dbapi.delete_account(context, **kwargs)

    def change_account_level(cls, context, **kwargs):
        LOG.debug('change account level: Received message from RPC.')
        return cls.dbapi.change_account_level(context, **kwargs)

    def charge_account(cls, context, **kwargs):
        LOG.debug('update account: Received message from RPC.')
        return cls.dbapi.charge_account(context,
                                        kwargs.pop('user_id'),
                                        # kwargs.pop('operator'),
                                        **kwargs)

    def update_account(cls, context, **kwargs):
        LOG.debug('update account: Received message from RPC.')
        return cls.dbapi.update_account(context,
                                        kwargs.pop('user_id'),
                                        **kwargs)

    def get_charges(cls, context, **kwargs):
        LOG.debug('get charges: Received message from RPC.')
        return cls.dbapi.get_charges(context, **kwargs)

    def get_charges_price_and_count(cls, context, **kwargs):
        LOG.debug('get_charges_price_and_count: Received message from RPC.')
        return cls.dbapi.get_charges_price_and_count(context, **kwargs)
