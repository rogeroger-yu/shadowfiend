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

from glanceclient import client as glance_client
from keystoneauth1 import loading as ks_loading

from oslo_config import cfg
from oslo_log import log

LOG = log.getLogger(__name__)
CONF = cfg.CONF


def drop_resource(service, resource_id):
    _glance_client = GlanceClient()
    if service == 'image':
        _glance_client.delete_image(resource_id)


class GlanceClient(object):
    def __init__(self):
        ks_loading.register_session_conf_options(CONF, "glance_client")
        ks_loading.register_auth_conf_options(CONF, "glance_client")
        self.auth = ks_loading.load_auth_from_conf_options(
            CONF,
            "glance_client")
        self.session = ks_loading.load_session_from_conf_options(
            CONF,
            "glance_client",
            auth=self.auth)
        self.glance_client = glance_client.Client(
            version='1',
            session=self.session,
            auth=self.auth)

    def delete_image(self, image_id, region_name=None):
        self.glance_client.images.delete(image_id)
