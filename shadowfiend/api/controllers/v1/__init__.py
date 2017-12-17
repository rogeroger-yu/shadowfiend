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
from wsmeext.pecan import wsexpose

from shadowfiend.api.controllers.v1 import account
from shadowfiend.api.controllers.v1 import project
from shadowfiend.api.controllers.v1 import relation
from shadowfiend.api.controllers.v1 import charge
from shadowfiend.api.controllers.v1 import order

from shadowfiend.api.controllers.v1 import models


class V1Controller(rest.RestController):
    accounts = account.AccountController()
    projects = project.ProjectController()
#    relations = relation.RelationController()
#    charges = charge.ChargeController()
#    orders = order.OrderController()

    @wsexpose(models.Version)
    def get(self):
        return models.Version(version='1.0.0')
