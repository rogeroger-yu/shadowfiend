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

from shadowfiend.api import acl
from shadowfiend.common import policy
from shadowfiend.processor.service import fetcher

from wsme import types as wtypes
from wsmeext.pecan import wsexpose

LOG = log.getLogger(__name__)
HOOK = pecan.request


class OrderController(rest.RestController):
    """The controller of resources."""

    _custom_actions = {
        'summary': ['GET'],
        'bills': ['GET'],
    }

    @wsexpose(wtypes.text, wtypes.text, bool)
    def summary(self, project_id=None, all_get=False):
        gnocchi_client = fetcher.GnocchiFetcher()
        policy.check_policy(HOOK.context, "order:summary",
                            action="order:summary")
        if not project_id and not all_get:
            project_id = HOOK.headers.get("X-Project-Id")
        if all_get and acl.context_is_admin(HOOK.headers):
            project_id = None
        try:
            result = gnocchi_client.get_summary(
                project_id)
        except Exception as e:
            LOG.error('Exception reason: %s' % e)
            raise
        return result

    @wsexpose(wtypes.text, wtypes.text, wtypes.text, int, wtypes.text, bool)
    def bills(self, resource_type, project_id=None,
              limit=None, marker=None, all_get=False):
        gnocchi_client = fetcher.GnocchiFetcher()
        policy.check_policy(HOOK.context, "order:bills",
                            action="order:bills")
        if not project_id and not all_get:
            project_id = HOOK.headers.get("X-Project-Id")
        if all_get and acl.context_is_admin(HOOK.headers):
            project_id = None
        try:
            resources = gnocchi_client.get_bills(
                resource_type, project_id, limit, marker)
        except Exception as e:
            LOG.error('Exception reason: %s' % e)
            raise
        return resources
