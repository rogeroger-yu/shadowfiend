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

from novaclient import client as nova_client
from novaclient.exceptions import NotFound

from oslo_config import cfg
from oslo_log import log

from shadowfiend.common import constants as const
from shadowfiend.common import timeutils
from shadowfiend.common import utils
from shadowfiend.services import BaseClient
from shadowfiend.services import Resource


LOG = log.getLogger(__name__)
CONF = cfg.CONF

SERVICE_CLIENT_OPTS = 'service_client'


def get_client(service):
    if service == 'compute':
        return NovaClient()


class NovaClient(BaseClient):
    def __init__(self):
        super(NovaClient, self).__init__()

        self.nova_client = nova_client.Client(
            version='2',
            session=self.session,
            auth_url=self.auth.auth_url)

    def flavor_list(self, is_public=True, region_name=None):
        return self.nova_client.flavors.list(is_public=is_public)

    def flavor_get(self, region_name, flavor_id):
        return self.nova_client.flavors.get(flavor_id)

    def image_get(self, region_name, image_id):
        return self.nova_client.images.get(image_id)

    def server_get(self, instance_id, region_name=None):
        try:
            server = self.nova_client.servers.get(instance_id)
        except NotFound:
            return None
        status = utils.transform_status(server.status)
        return Server(id=server.id,
                      name=server.name,
                      status=status,
                      original_status=server.status,
                      resource_type=const.RESOURCE_INSTANCE,
                      flavor=server.flavor)

    def server_delete(self, instance_id):
        try:
            self.nova_client.servers.delete(instance_id)
        except NotFound:
            return None
        return True

    def server_list_by_resv_id(self, resv_id,
                               region_name=None, detailed=False):
        search_opts = {'reservation_id': resv_id,
                       'all_tenants': 1}
        return self.nova_client.servers.list(detailed, search_opts)

    def server_list(self, project_id, region_name=None,
                    detailed=True, project_name=None):
        search_opts = {'all_tenants': 1,
                       'project_id': project_id}
        servers = self.nova_client.servers.list(detailed, search_opts)
        formatted_servers = []
        for server in servers:
            flavor = self.flavor_get(region_name, server.flavor['id'])
            image = self.image_get(region_name, server.image['id'])
            created_at = utils.format_datetime(server.created)
            status = utils.transform_status(server.status)
            formatted_servers.append(
                Server(id=server.id,
                       name=server.name,
                       flavor_name=flavor.name,
                       flavor_id=flavor.id,
                       disk_gb=(getattr(image, "OS-EXT-IMG-SIZE:size") /
                                (1024 * 1024 * 1024)),
                       image_name=image.name,
                       image_id=image.id,
                       status=status,
                       original_status=server.status,
                       resource_type=const.RESOURCE_INSTANCE,
                       user_id=server.user_id,
                       project_id=server.tenant_id,
                       project_name=project_name,
                       created_at=created_at))
        return formatted_servers

    def drop_resource(self, resource_id):
        return self.server_delete(resource_id)


class Server(Resource):
    def to_message(self):
        msg = {
            'event_type': 'compute.instance.create.end.again',
            'payload': {
                'instance_type': self.flavor_name,
                'disk_gb': self.disk_gb,
                'instance_id': self.id,
                'display_name': self.name,
                'user_id': self.user_id,
                'tenant_id': self.project_id,
                'image_name': self.image_name,
                'image_meta': {
                    'base_image_ref': self.image_id
                }
            },
            'timestamp': utils.format_datetime(timeutils.strtime())
        }
        return msg

    def to_env(self):
        return dict(HTTP_X_USER_ID=self.user_id,
                    HTTP_X_PROJECT_ID=self.project_id)

    def to_body(self):
        body = {}
        body['server'] = dict(imageRef=self.image_id, flavorRef=self.flavor_id)
        return body
