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

import json
import re

from oslo_config import cfg
from shadowfiend.common import constants as const
from shadowfiend.middleware import base
from shadowfiend.services.glance import GlanceClient
from stevedore import extension


UUID_RE = (r"([0-9a-f]{32}|[0-9a-z]{8}-[0-9a-z]{4}-"
           "[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})")
API_VERSION = r"(v1|v2)"
RESOURCE_RE = r"(images)"


class SizeItem(base.ProductItem):
    service = const.SERVICE_BLOCKSTORAGE

    def get_product_name(self, body):
        return const.PRODUCT_SNAPSHOT_SIZE

    def get_resource_volume(self, env, body):
        base_image_id = env.get('HTTP_X_IMAGE_META_PROPERTY_BASE_IMAGE_REF')
        if not base_image_id:
            return 0
        image = GlanceClient.image_get(
            base_image_id,
            cfg.CONF.billing.region_name)
        return int(image.size) / (1024 ** 3)


class GlanceBillingProtocol(base.BillingProtocol):

    def __init__(self, app, conf):
        super(GlanceBillingProtocol, self).__init__(app, conf)
        self.resource_regex = re.compile(
            r"^/%s/%s/%s([.][^.]+)?$" %
            (API_VERSION, RESOURCE_RE, UUID_RE), re.UNICODE)
        self.create_resource_regex = re.compile(
            r"^/%s/%s([.][^.]+)?$" %
            (API_VERSION, RESOURCE_RE), re.UNICODE)
        self.position = 2
        self.resource_regexs = [
            self.resource_regex,
        ]

        self.product_items = extension.ExtensionManager(
            namespace='shadowfiend.snapshot.product_items',
            invoke_on_load=True,
            invoke_args=(self.gclient,))

    def parse_app_result(self, body, result, user_id, project_id):
        resources = []
        try:
            result = json.loads(result[0])
            resources.append(base.Resource(
                resource_id=result['image']['id'],
                resource_name=result['image']['name'],
                type=const.RESOURCE_IMAGE,
                status=const.STATE_RUNNING,
                user_id=user_id,
                project_id=project_id))
        except Exception:
            return []
        return resources


def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)

    def bill_filter(app):
        return GlanceBillingProtocol(app, conf)
    return bill_filter
