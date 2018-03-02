# Copyright 2014 Rackspace Hosting
# All Rights Reserved.
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

from shadowfiend.tests.unit.db import utils as db_utils
from shadowfiend.db import models as db_models
from shadowfiend.db import api as dbapi

dbapi = dbapi.get_instance()


def _create_temp_account(**kwargs):
    db_account = db_utils.get_test_account(**kwargs)
    account = db_models.Account(**db_account)
    return account


def _create_temp_project(**kwargs):
    db_project = db_utils.get_test_project(**kwargs)
    project = db_models.Project(**db_project)
    return project


def _create_temp_relation(**kwargs):
    db_relation = db_utils.get_test_relation(**kwargs)
    relation = db_models.UsrPrjRelation(**db_relation)
    return relation


def create_test_account(context, *args, **kwargs):
    account = _create_temp_account(**kwargs)
    dbapi.create_account(context, account)
    return account


def get_test_account(_bond, context, user_id, *args, **kwargs):
    return dbapi.get_account(context, user_id, *args, **kwargs)


def get_test_accounts(_bond, context, *args, **kwargs):
    return dbapi.get_accounts(context, **kwargs)


def update_test_account(_bond, context, *args, **kwargs):
    return dbapi.update_account(context, **kwargs)


def _create_temp_charge(user_id, **kwargs):
    kwargs['user_id'] = user_id
    db_charge = db_utils.get_test_charge(**kwargs)
    # charge = db_models.Charge(**db_charge)
    return db_charge


def create_test_charge(context, user_id, **kwargs):
    charge = _create_temp_charge(user_id, **kwargs)
    dbapi.charge_account(context, **charge)
    return charge


def get_test_charges(context, *args, **kwargs):
    return dbapi.get_charges(context, **kwargs)


def get_test_charges_price_and_count(context, *args, **kwargs):
    return dbapi.get_charges_price_and_count(context, **kwargs)


def charge_test_account(_bond, context, *args, **kwargs):
    return dbapi.charge_account(context, *args, **kwargs)


def change_test_account_level(_bond, context, *args, **kwargs):
    return dbapi.change_account_level(context, *args, **kwargs)


def delete_test_account(_bond, context, user_id, *args, **kwargs):
    return dbapi.delete_account(context, user_id, *args, **kwargs)


def create_test_project(context, *args, **kwargs):
    project = _create_temp_project(**kwargs)
    dbapi.create_project(context, project)
    return project


def create_test_relation(context, *args, **kwargs):
    relation = _create_temp_relation(**kwargs)
    dbapi.change_billing_owner(context, relation.project_id, relation.user_id)
    return relation
