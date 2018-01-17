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
from pecan import rest

from shadowfiend.api.controllers import base
from shadowfiend.api.controllers import link
from shadowfiend.api.controllers.v1 import account
from shadowfiend.api.controllers.v1 import download
from shadowfiend.api.controllers.v1 import order
from shadowfiend.api.controllers.v1 import project

from wsmeext.pecan import wsexpose
from wsme import types as wtypes


class MediaType(base.APIBase):
    """A media type representation."""

    base = wtypes.text
    type = wtypes.text

    def __init__(self, base, type):
        self.base = base
        self.type = type


class V1(base.APIBase):
    id = wtypes.text
    media_types = [MediaType]
    links = [link.Link]
    accounts = [link.Link]
    downloads = [link.Link]
    projects = [link.Link]
    orders = [link.Link]

    @staticmethod
    def convert():
        v1 = V1()
        v1.id = "v1"
        v1.links = [link.Link.make_link('self', pecan.request.host_url,
                                        'v1', '', bookmark=True),
                    link.Link.make_link('describedby',
                                        'http://docs.openstack.org',
                                        'developer/shadowfiend/dev',
                                        'api-spec-v1.html',
                                        bookmark=True, type='text/html')]
        v1.media_types = [MediaType(
            'application/json',
            'application/vnd.openstack.shadowfiend.v1+json')]
        v1.accounts = [link.Link.make_link('self', pecan.request.host_url,
                                           'accounts', '')]
        v1.downloads = [link.Link.make_link('self', pecan.request.host_url,
                                            'downloads', '')]
        v1.projects = [link.Link.make_link('self', pecan.request.host_url,
                                           'projects', '')]
        v1.orders = [link.Link.make_link('self', pecan.request.host_url,
                                         'orders', '')]
        return v1


class Controller(rest.RestController):
    accounts = account.AccountController()
    downloads = download.DownloadsController()
    projects = project.ProjectController()
    orders = order.OrderController()

    @wsexpose(V1)
    def get(self):
        return V1.convert()
