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

import datetime
import pecan

from oslo_config import cfg
from oslo_log import log
from pecan import rest

from shadowfiend.api import acl
from shadowfiend.api.controllers.v1 import models
from shadowfiend.common import exception
from shadowfiend.common import policy
from shadowfiend.common import utils as shadowutils
from shadowfiend.db import models as db_models
from shadowfiend.processor.service import fetcher
from shadowfiend.services import keystone as ks_client

from wsme import types as wtypes
from wsmeext.pecan import wsexpose


LOG = log.getLogger(__name__)
HOOK = pecan.request
CONF = cfg.CONF
CONF.import_opt('cloudkitty_period',
                'shadowfiend.processor.config',
                'processor')


class ExistAccountController(rest.RestController):
    """Manages operations on account."""

    _custom_actions = {
        'level': ['PUT'],
        'charges': ['GET'],
        'estimate': ['GET'],
    }

    def __init__(self, user_id):
        self._id = user_id
        self.gnocchi_fetcher = fetcher.GnocchiFetcher()

    def _account(self, user_id=None):
        _id = user_id or self._id
        try:
            account = HOOK.conductor_rpcapi.get_account(HOOK.context,
                                                        _id)
        except exception.AccountNotFound:
            LOG.error("Account %s not found" % _id)
            raise
        except exception.GetExternalBalanceFailed:
            raise
        except (Exception):
            LOG.error("Fail to get account %s" % _id)
            raise exception.AccountGetFailed(user_id=_id)
        return account

    @wsexpose(models.Charge, wtypes.text, body=models.Charge)
    def put(self, data):
        """Charge the account."""
        policy.check_policy(HOOK.context, "account:charge")

        # check accountant charge value
        lacv = int(CONF.limited_accountant_charge_value)
        if data.value < -lacv or data.value > lacv:
            raise exception.InvalidChargeValue(value=data.value)

        # remarks = data.remarks if data.remarks != wsme.Unset else None
        operator = HOOK.context.user_id

        try:
            charge = HOOK.conductor_rpcapi.update_account(
                HOOK.context,
                self._id,
                operator=operator,
                **data.as_dict())

        except exception.NotAuthorized as e:
            LOG.error('Fail to charge the account:%s'
                      'due to not authorization' % self._id)
            raise exception.NotAuthorized()
        except Exception as e:
            LOG.error('Fail to charge the account:%s,'
                      'charge value: %s' % (self._id, data.value))
            raise exception.DBError(reason=e)
        # else:
        #     # Notifier account
        #     if CONF.notify_account_charged:
        #         account = HOOK.conductor_rpcapi.get_account(HOOK.context,
        #                                                     self._id).as_dict()
        #         contact = kunkka.get_uos_user(account['user_id'])
        #         language = CONF.notification_language
        #         self.notifier = notifier.NotifierService(
        #             CONF.checker.notifier_level)
        #         self.notifier.notify_account_charged(
        #             HOOK.context, account, contact,
        #             data['type'], charge.value,
        #             bonus=bonus.value if has_bonus else 0,
        #             operator=operator,
        #             operator_name=HOOK.context.user_name,
        #             remarks=remarks, language=language)
        return models.Charge.from_db_model(charge)

    @wsexpose(models.UserAccount)
    def get(self):
        """Get this account."""
        user_id = acl.get_limited_to_user(
            HOOK.headers, 'account:get') or self._id
        return db_models.Account(**self._account(user_id=user_id))

    @wsexpose(None)
    def delete(self):
        """Delete the account including the projects that belong to it."""
        policy.check_policy(HOOK.context, "account:delete")
        try:
            HOOK.conductor_rpcapi.delete_account(HOOK.context,
                                                 self._id)
        except (exception.NotFound):
            LOG.Warning('Could not find account whose user_id is %s' %
                        self._id)

    @wsexpose(models.UserAccount, int)
    def level(self, level):
        """Update the account's level."""
        policy.check_policy(HOOK.context, "account:level")

        if not isinstance(level, int) or level < 0 or level > 9:
            raise exception.InvalidParameterValue(err="Invalid Level")
        try:
            account = HOOK.conductor_rpcapi.change_account_level(
                HOOK.context, self._id, level)
        except Exception as e:
            LOG.error('Fail to change the account level of: %s' % self._id)
            raise exception.DBError(reason=e)

        return models.UserAccount(**account)

    @wsexpose(models.Charges, wtypes.text, datetime.datetime,
              datetime.datetime, int, int)
    def charges(self, type=None, start_time=None,
                end_time=None, limit=None, offset=None):
        """Get this account's charge records."""
        policy.check_policy(HOOK.context, "charges:get")

        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")
        if offset and offset < 0:
            raise exception.InvalidParameterValue(err="Invalid offset")

        user_id = acl.get_limited_to_user(
            HOOK.headers, 'account:charge') or self._id

        charges = HOOK.conductor_rpcapi.get_charges(HOOK.context,
                                                    user_id=user_id,
                                                    type=type,
                                                    limit=limit,
                                                    offset=offset,
                                                    start_time=start_time,
                                                    end_time=end_time)
        charges_list = []
        for charge in charges:
            charges_list.append(models.Charge(**charge))

        total_price, total_count = (HOOK.conductor_rpcapi.
                                    get_charges_price_and_count(
                                        HOOK.context,
                                        user_id=user_id,
                                        type=type,
                                        start_time=start_time,
                                        end_time=end_time))

        return models.Charges.transform(total_price=total_price,
                                        total_count=total_count,
                                        charges=charges_list)

    @wsexpose(models.Estimate)
    def estimate(self):
        """Get the price per day and the remaining days."""

        user_id = acl.get_limited_to_user(
            HOOK.headers, 'account:estimate') or self._id

        account = self._account(user_id=user_id)
        price_per_hour = self.gnocchi_fetcher.get_current_consume(
            HOOK.context.project_id)

        if price_per_hour == 0:
            if account['balance'] < 0:
                return models.Estimate(price_per_hour=price_per_hour,
                                       remaining_day=-2)
            else:
                return models.Estimate(price_per_hour=price_per_hour,
                                       remaining_day=-1)
        elif price_per_hour > 0:
            if account['balance'] < 0:
                return models.Estimate(price_per_hour=price_per_hour,
                                       remaining_day=-2)
            else:
                price_per_day = price_per_hour * 24
                remaining_day = int(account['balance'] / price_per_day)

        return models.Estimate(balance=account['balance'],
                               price_per_hour=price_per_hour,
                               remaining_day=remaining_day)


class ChargeController(rest.RestController):

    @wsexpose(models.Charges, wtypes.text, wtypes.text,
              datetime.datetime, datetime.datetime, int, int,
              wtypes.text, wtypes.text)
    def get(self, user_id=None, type=None, start_time=None,
            end_time=None, limit=None, offset=None,
            sort_key='created_at', sort_dir='desc'):
        """Get all charges of all account."""

        policy.check_policy(HOOK.context, "charges:all")

        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")
        if offset and offset < 0:
            raise exception.InvalidParameterValue(err="Invalid offset")

        users = {}

        def _get_user(user_id):
            user = users.get(user_id)
            if user:
                return user
            contact = ks_client.get_user(user_id) or {}
            user_name = contact.get('name')
            email = contact.get('email')
            users[user_id] = models.User(user_id=user_id,
                                         user_name=user_name,
                                         email=email)
            return users[user_id]

        charges = HOOK.conductor_rpcapi.get_charges(
            HOOK.context,
            user_id=user_id,
            type=type,
            limit=limit,
            offset=offset,
            start_time=start_time,
            end_time=end_time,
            sort_key=sort_key,
            sort_dir=sort_dir)
        charges_list = []
        for charge in charges:
            acharge = models.Charge.from_db_model(charge)
            acharge.target = _get_user(charge['user_id'])
            charges_list.append(acharge)

        total_price, total_count = (HOOK.conductor_rpcapi.
                                    get_charges_price_and_count(
                                        HOOK.context,
                                        user_id=user_id,
                                        type=type,
                                        start_time=start_time,
                                        end_time=end_time))

        return models.Charges.transform(total_price=total_price,
                                        total_count=total_count,
                                        charges=charges_list)


class TransferMoneyController(rest.RestController):

    @wsexpose(None, body=models.TransferMoneyBody)
    def post(self, data):
        """Transfer money from one account to another.

        And only the domain owner can do the operation.
        """
        is_domain_owner = acl.context_is_domain_owner(HOOK.headers)
        if not is_domain_owner:
            raise exception.NotAuthorized()

        HOOK.conductor_rpcapi.transfer_money(HOOK.context, data)


class AccountController(rest.RestController):
    """Manages operations on account."""

    charges = ChargeController()
    transfer = TransferMoneyController()

    @pecan.expose()
    def _lookup(self, user_id, *remainder):
        if remainder and not remainder[-1]:
            remainder = remainder[:-1]
        _correct = len(user_id) == 32 or len(user_id) == 64
        if _correct:
            return ExistAccountController(user_id), remainder

    @wsexpose(None, body=models.AdminAccount)
    def post(self, data):
        """Create a new account."""
        policy.check_policy(HOOK.context, "account:post")
        try:
            account = data.as_dict()
            response = HOOK.conductor_rpcapi.create_account(HOOK.context,
                                                            account)
            return response
        except Exception:
            LOG.error('Fail to create account: %s' % data.as_dict())

    @wsexpose(models.AdminAccounts, bool, int, int, wtypes.text)
    def get_all(self, owed=None, limit=None, offset=None, duration=None):
        """Get this account."""
        policy.check_policy(HOOK.context, "account:all")

        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")
        if offset and offset < 0:
            raise exception.InvalidParameterValue(err="Invalid offset")

        duration = shadowutils.normalize_timedelta(duration)
        if duration:
            active_from = datetime.datetime.utcnow() - duration
        else:
            active_from = None

        try:
            accounts = HOOK.conductor_rpcapi.get_accounts(
                HOOK.context,
                owed=owed,
                limit=limit,
                offset=offset,
                active_from=active_from)
            count = HOOK.conductor_rpcapi.get_accounts_count(
                HOOK.context,
                owed=owed,
                active_from=active_from)
        except exception.NotAuthorized as e:
            LOG.error('Failed to get all accounts')
            raise exception.NotAuthorized()
        except Exception as e:
            LOG.error('Failed to get all accounts')
            raise exception.DBError(reason=e)

        accounts = [models.AdminAccount.transform(**account)
                    for account in accounts]

        return models.AdminAccounts.transform(total_count=count,
                                              accounts=accounts)
