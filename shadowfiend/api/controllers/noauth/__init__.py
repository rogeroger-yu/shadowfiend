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

from shadowfiend.api import expose

from shadowfiend.api.controllers.noauth import account
from shadowfiend.api.controllers.noauth import project
from shadowfiend.api.controllers.v1 import models


class NoAuthController(rest.RestController):
    accounts = account.AccountController()
    projects = project.ProjectController()

    @expose.expose(models.Version)
    def get(self):
        return models.Version(version='noauth')