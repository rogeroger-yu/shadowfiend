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

from oslo_log import log
from shadowfiend.db import api as dbapi
from shadowfiend.db import models as db_models

LOG = log.getLogger(__name__)


class Handler(object):

    dbapi = dbapi.get_instance()

    def get_billing_owner(cls, context, **kwargs):
        LOG.debug('Conductor Function: get_billing_owner.')
        billing_owner = cls.dbapi.get_billing_owner(context,
                                                    kwargs['project_id'])
        return billing_owner

    def change_billing_owner(cls, context, **kwargs):
        LOG.debug('Conductor Function: change_billing_owner.')
        cls.dbapi.change_billing_owner(context,
                                       kwargs['project_id'],
                                       kwargs['user_id'])

    def create_project(cls, context, **kwargs):
        LOG.debug('Conductor Function: create_project.')
        project = db_models.Project(**kwargs)
        return cls.dbapi.create_project(context, project)

    def get_project(cls, context, **kwargs):
        LOG.debug('Conductor Function: get_project.')
        project = cls.dbapi.get_project(context, kwargs['project_id'])
        return project

    def delete_project(cls, context, **kwargs):
        LOG.debug('Conductor Function: delete_project.')
        cls.dbapi.delete_project(context, kwargs['project_id'])

    def get_relation(cls, context, **kwargs):
        LOG.debug('Conductor Function: get_user_projects.')
        return cls.dbapi.get_relation(context, **kwargs)

    def get_projects(cls, context, **kwargs):
        LOG.debug('Conductor Function: get_projects.')
        return cls.dbapi.get_projects(context, **kwargs)
