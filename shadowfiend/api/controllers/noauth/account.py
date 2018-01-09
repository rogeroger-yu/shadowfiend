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

from oslo_log import log
from pecan import rest

from shadowfiend.api.controllers.v1 import models
from shadowfiend.common import exception

from wsmeext.pecan import wsexpose


LOG = log.getLogger(__name__)

HOOK = pecan.request


class AccountController(rest.RestController):
    """Manages operations on the accounts collection."""

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
