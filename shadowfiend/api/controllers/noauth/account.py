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

import pecan

from oslo_config import cfg
from oslo_log import log
from pecan import rest

from shadowfiend.api.controllers.v1 import models
from shadowfiend.common import exception

from wsme import types as wtypes
from wsmeext.pecan import wsexpose


CONF = cfg.CONF
LOG = log.getLogger(__name__)

HOOK = pecan.request


class ExistAccountController(rest.RestController):
    """Manages operations on account."""

    def __init__(self, user_id):
        self._id = user_id

    @wsexpose(models.Charge, wtypes.text, body=models.Charge)
    def put(self, data):
        """Charge the account."""
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
        return models.Charge.from_db_model(charge)


class AccountController(rest.RestController):
    """Manages operations on the accounts collection."""

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
        try:
            account = data.as_dict()
            return HOOK.conductor_rpcapi.create_account(HOOK.context,
                                                        account)
        except Exception:
            LOG.ERROR('Fail to create account: %s' % data.as_dict())
            raise exception.AccountCreateFailed(user_id=data.user_id,
                                                domain_id=data.domain_id)
