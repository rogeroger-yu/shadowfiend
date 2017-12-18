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
import json

import pecan
import wsme
from pecan import rest
from wsme import types as wtypes
from wsmeext.pecan import wsexpose
from oslo_config import cfg
from oslo_log import log

from shadowfiend.api import acl
from shadowfiend.api.controllers.v1 import models
from shadowfiend.db import models as db_models
from shadowfiend.conductor import api as conductor_api
from shadowfiend.common import policy
from shadowfiend.common import exception


LOG = log.getLogger(__name__)
HOOK = pecan.request

class ExistAccountController(rest.RestController):
    """Manages operations on account."""

    _custom_actions = {
        'level': ['PUT'],
        'charges': ['GET'],
        'estimate': ['GET'],
        'estimate_per_day': ['GET'],
    }

    def __init__(self, user_id):
        self._id = user_id

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
        lacv = int(cfg.CONF.limited_accountant_charge_value)
        if data.value < -lacv or data.value > lacv:
            raise exception.InvalidChargeValue(value=data.value)

        remarks = data.remarks if data.remarks != wsme.Unset else None
        operator = HOOK.context.user_id

        try:
            charge, is_first_charge = HOOK.conductor_rpcapi.\
                    update_account(HOOK.context,
                                   self._id,
                                   operator=operator,
                                   **data.as_dict())

        except exception.NotAuthorized as e:
            LOG.error('Fail to charge the account:%s '
                          'due to not authorization' % self._id)
            raise exception.NotAuthorized()
        except Exception as e:
            LOG.error('Fail to charge the account:%s, '
                          'charge value: %s' % (self._id, data.value))
            raise exception.DBError(reason=e)
        #else:
        #    # Notifier account
        #    if cfg.CONF.notify_account_charged:
        #        account = HOOK.conductor_rpcapi.get_account(HOOK.context,
        #                                                    self._id).as_dict()
        #        contact = kunkka.get_uos_user(account['user_id'])
        #        language = cfg.CONF.notification_language
        #        self.notifier = notifier.NotifierService(
        #            cfg.CONF.checker.notifier_level)
        #        self.notifier.notify_account_charged(
        #            HOOK.context, account, contact,
        #            data['type'], charge.value,
        #            bonus=bonus.value if has_bonus else 0,
        #            operator=operator,
        #            operator_name=HOOK.context.user_name,
        #            remarks=remarks, language=language)
        return models.Charge.from_db_model(charge)

    @wsexpose(models.UserAccount)
    def get(self):
        """Get this account."""
        user_id = acl.get_limited_to_user(
            HOOK.headers, 'account_get') or self._id
        return db_models.Account(**self._account(user_id=user_id))

    @wsexpose(None)
    def delete(self):
        """Delete the account including the projects that belong to it."""
        policy.check_policy(HOOK.context, "account:delete")
        try:
            HOOK.conductor_rpcapi.delete_account(HOOK.context,
                                                 self._id)
        except (exception.NotFound):
            msg = _('Could not find account whose user_id is %s' % self._id)
        except Exception:
            LOG.error('Fail to create account: %s' % data.as_dict())

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

        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")
        if offset and offset < 0:
            raise exception.InvalidParameterValue(err="Invalid offset")

        user_id = acl.get_limited_to_user(
            HOOK.headers, 'account_charge') or self._id

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

        total_price, total_count = HOOK.conductor_rpcapi.\
                get_charges_price_and_count(HOOK.context,
                                            user_id=user_id,
                                            type=type,
                                            start_time=start_time,
                                            end_time=end_time)

        return models.Charges.transform(total_price=total_price,
                                        total_count=total_count,
                                        charges=charges_list)

    @wsexpose(int)
    def estimate(self):
        """Estimate the hourly billing resources how many days to owed.
        """
        if not cfg.CONF.enable_owe:
            return -1

        user_id = acl.get_limited_to_user(
            HOOK.headers, 'account_estimate') or self._id

        account = self._account(user_id=user_id)
        if account.balance < 0:
            return -2

        orders = HOOK.conductor_rpcapi.get_active_orders(HOOK.context,
                                                         user_id=user_id,
                                                         within_one_hour=True,
                                                         bill_methods=['hour'])
        if not orders:
            return -1

        price_per_hour = 0
        for order in orders:
            price_per_hour += gringutils._quantize_decimal(order.unit_price)

        if price_per_hour == 0:
            return -1

        price_per_day = price_per_hour * 24
        days_to_owe_d = float(account.balance / price_per_day)
        days_to_owe = round(days_to_owe_d)
        if days_to_owe < days_to_owe_d:
            days_to_owe = days_to_owe + 1
        if days_to_owe > 7:
            return -1
        return days_to_owe

    @wsexpose(models.Estimate)
    def estimate_per_day(self):
        """Get the price per day and the remaining days that the
        balance can support.
        """
        user_id = acl.get_limited_to_user(
            HOOK.headers, 'account_estimate') or self._id

        account = self._account(user_id=user_id)
        orders = HOOK.conductor_rpcapi.get_active_orders(HOOK.context,
                                                         user_id=user_id,
                                                         within_one_hour=True,
                                                         bill_methods=['hour'])
        price_per_day = gringutils._quantize_decimal(0)
        if not orders:
            if account.balance < 0:
                return (price_per_day, -2)
            else:
                return (price_per_day, -1)

        price_per_hour = 0
        for order in orders:
            price_per_hour += gringutils._quantize_decimal(order.unit_price)

        if price_per_hour == 0:
            if account.balance < 0:
                return (price_per_day, -2)
            else:
                return (price_per_day, -1)
        elif price_per_hour > 0:
            if account.balance < 0:
                return (price_per_day, -2)
            else:
                price_per_day = price_per_hour * 24
                remaining_day = int(account.balance / price_per_day)

        return models.Estimate(price_per_day=price_per_day,
                               remaining_day=remaining_day)


class ChargeController(rest.RestController):

    @wsexpose(models.Charges, wtypes.text, wtypes.text,
              datetime.datetime, datetime.datetime, int, int,
              wtypes.text, wtypes.text)
    def get(self, user_id=None, type=None, start_time=None,
            end_time=None, limit=None, offset=None,
           sort_key='created_at', sort_dir='desc'):
        """Get all charges of all account."""

        check_policy(HOOK.context, "charges:all")

        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")
        if offset and offset < 0:
            raise exception.InvalidParameterValue(err="Invalid offset")

        users = {}

        def _get_user(user_id):
            user = users.get(user_id)
            if user:
                return user
            contact = kunkka.get_uos_user(user_id) or {}
            user_name = contact.get('name')
            email = contact.get('email')
            real_name = contact.get('real_name')
            mobile = contact.get('phone')
            company = contact.get('company')
            users[user_id] = models.User(user_id=user_id,
                                         user_name=user_name,
                                         email=email,
                                         real_name=real_name,
                                         mobile=mobile,
                                         company=company)
            return users[user_id]

        charges = HOOK.conductor_rpcapi.get_charges(HOOK.context,
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
            acharge.actor = _get_user(charge.operator)
            acharge.target = _get_user(charge.user_id)
            charges_list.append(acharge)

        total_price, total_count = HOOK.conductor_rpcapi.\
                get_charges_price_and_count(HOOK.context,
                                            user_id=user_id,
                                            type=type,
                                            start_time=start_time,
                                            end_time=end_time)
        total_price = gringutils._quantize_decimal(total_price)

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

    @wsexpose(models.UserAccount, bool, int, int, wtypes.text)
    def get_all(self, owed=None, limit=None, offset=None):
        """Get this account."""
        policy.check_policy(HOOK.context, "account:all")

        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")
        if offset and offset < 0:
            raise exception.InvalidParameterValue(err="Invalid offset")

        try:
            accounts = HOOK.conductor_rpcapi.get_accounts(HOOK.context,
                                                          **data.as_dict())
            count = HOOK.conductor_rpcapi.get_accounts_count(HOOK.context,
                                                             **data.as_dict())
        except exception.NotAuthorized as e:
            LOG.ERROR('Failed to get all accounts')
            raise exception.NotAuthorized()
        except Exception as e:
            LOG.ERROR('Failed to get all accounts')
            raise exception.DBError(reason=e)

        accounts = [models.AdminAccount.from_db_model(account)
                    for account in accounts]

        return models.AdminAccounts(total_count=count,
                                    accounts=accounts)


