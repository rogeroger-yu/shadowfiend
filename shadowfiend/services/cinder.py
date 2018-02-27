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

import time

from oslo_config import cfg
from oslo_log import log

from cinderclient import client as cinder_client
from shadowfiend.services import BaseClient
from shadowfiend.common.exception import NotFound


LOG = log.getLogger(__name__)
CONF = cfg.CONF

SERVICE_CLIENT_OPTS = 'service_client'


def drop_resource(service, resource_id):
    _volume_client = CinderClient()
    if service == 'volume.volume':
        _volume_client.delete_volume(resource_id)
    elif service == 'volume.snapshot':
        _volume_client.delete_snapshot(resource_id)


class CinderClient(BaseClient):
    def __init__(self):
        super(CinderClient, self).__init__()

        self.cinder_client = cinder_client.Client(
            version='1',
            session=self.session,
            auth_url=self.auth.auth_url)

    def get_volume(self, volume_id, region_name=None):
        try:
            volume = self.cinder_client.volumes.get(volume_id)
        except NotFound:
            return None
        return dict(id=volume.id,
                    name=volume.display_name,
                    original_status=volume.status,
                    attachments=volume.attachments,
                    size=volume.size)

    def delete_volume(self, volume_id, region_name=None):
        search_opts = {'all_tenants': 1, 'volume_id': volume_id}
        snaps = self.cinder_client.volume_snapshots.list(
            detailed=False,
            search_opts=search_opts)
        for snap in snaps:
            try:
                self.cinder_client.volume_snapshots.delete(snap)
            except Exception:
                pass
        volume = self.get_volume(volume_id, region_name=region_name)
        for attachment in volume['attachments']:
            try:
                self.cinder_client.volumes.detach(volume_id,
                                                  attachment['attachment_id'])
            except Exception:
                pass

        # wait 10 seconds to delete this volume
        time.sleep(10)
        self.cinder_client.volumes.delete(volume_id)

    def delete_snapshot(self, snap_id, region_name=None):
        self.cinder_client.volume_snapshots.delete(snap_id)
