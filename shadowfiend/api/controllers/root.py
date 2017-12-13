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

from pecan import rest
from wsme import types as wtypes

from shadowfiend.api.controllers import v1
from shadowfiend.api.controllers import noauth
from shadowfiend.api import expose


class RootController(rest.RestController):

    _versions = ['v1']

    _default_version = 'v1'

    v1 = v1.V1Controller()
    noauth = noauth.NoAuthController()

    @expose.expose(wtypes.text)
    def get(self):
        return "test"
