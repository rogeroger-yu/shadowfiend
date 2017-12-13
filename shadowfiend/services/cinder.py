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

from oslo_config import cfg
from oslo_log import log

from cinderclient import client as cinder_client
from shadowfiend.services import BaseClient
from shadowfiend.services import Resource
from shadowfiend.common import constants as const
from shadowfiend.common import utils


LOG = log.getLogger(__name__)
CONF = cfg.CONF

SERVICE_CLIENT_OPTS = 'service_client'


class CinderClient(BaseClient):
    def __init__(self):
        super(CinderClient, self).__init__()

        self.cinder_client = cinder_client.Client(
            version='1',
            session=self.session,
            auth_url=self.auth.auth_url)

    def volume_get(volume_id, region_name=None):
        try:
            volume = self.cinder_client.volumes.get(volume_id)
        except NotFound:
            return None
        status = utils.transform_status(volume.status)
        return Volume(id=volume.id,
                      name=volume.display_name,
                      status=status,
                      original_status=volume.status,
                      resource_type=const.RESOURCE_VOLUME,
                      attachments=volume.attachments,
                      size=volume.size)

    def snapshot_get(snapshot_id, region_name=None):
        try:
            sp = self.cinder_client.volume_snapshots.get(snapshot_id)
        except NotFound:
            return None
        status = utils.transform_status(sp.status)
        return Snapshot(id=sp.id,
                        name=sp.display_name,
                        size=sp.size,
                        status=status,
                        original_status=sp.status,
                        resource_type=const.RESOURCE_SNAPSHOT)


class Snapshot(Resource):
    def to_message(self):
        msg = {
            'event_type': 'snapshot.create.end.again',
            'payload': {
                'snapshot_id': self.id,
                'display_name': self.name,
                'volume_size': self.size,
                'user_id': self.user_id,
                'tenant_id': self.project_id
            },
            'timestamp': utils.format_datetime(timeutils.strtime())
        }
        return msg

    def to_env(self):
        return dict(HTTP_X_USER_ID=self.user_id, HTTP_X_PROJECT_ID=self.project_id)

    def to_body(self):
        body = {}
        body[self.resource_type] = dict(snapshot_id=self.id)
        return body


class Volume(Resource):
    def to_message(self):
        msg = {
            'event_type': 'volume.create.end.again',
            'payload': {
                'volume_id': self.id,
                'display_name': self.name,
                'size': self.size,
                'volume_type': self.type,
                'user_id': self.user_id,
                'tenant_id': self.project_id
            },
            'timestamp': utils.format_datetime(timeutils.strtime())
        }
        return msg

    def to_env(self):
        """
        :returns: TODO
        """
        return dict(HTTP_X_USER_ID=self.user_id, HTTP_X_PROJECT_ID=self.project_id)

    def to_body(self):
        body = {}
        body[self.resource_type] = dict(volume_type=self.type, size=self.size)
        return body
