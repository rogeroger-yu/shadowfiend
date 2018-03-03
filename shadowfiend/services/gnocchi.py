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

import json
import six

from oslo_config import cfg
from oslo_log import log

from gnocchiclient import client as gnocchi_client
from gnocchiclient import exceptions as gexceptions
from shadowfiend.services import BaseClient


LOG = log.getLogger(__name__)
CONF = cfg.CONF

CONF.import_opt('cloudkitty_period',
                'shadowfiend.processor.config',
                'processor')

SHADOWFIEND_STATE_RESOURCE = 'shadowfiend_state'


class GnocchiClient(BaseClient):
    def __init__(self):
        super(GnocchiClient, self).__init__()

        self.gnocchi_client = gnocchi_client.Client(
            version='1',
            session=self.session,
            auth=self.auth)

    def init_storage_backend(self):
        _archive_policy_definition = json.loads(
            '[{"granularity": ' +
            six.text_type(CONF.processor.cloudkitty_period) +
            ', "timespan": "90 days"}, '
            '{"granularity": 86400, "timespan": "360 days"}, '
            '{"granularity": 2592000, "timespan": "1800 days"}]')

        # Creates rating archive-policy if not exists
        try:
            self.gnocchi_client.archive_policy.get('billing')
        except gexceptions.ArchivePolicyNotFound:
            ck_policy = {}
            ck_policy["name"] = 'billing'
            ck_policy["back_window"] = 0
            ck_policy["aggregation_methods"] = ["sum", ]
            ck_policy["definition"] = _archive_policy_definition
            self.gnocchi_client.archive_policy.create(ck_policy)
        # Creates state resource if it doesn't exist
        try:
            self.gnocchi_client.resource_type.create(
                {'name': SHADOWFIEND_STATE_RESOURCE})
        except gexceptions.ResourceAlreadyExists:
            pass
