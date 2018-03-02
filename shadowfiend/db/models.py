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

"""Model classes for use in the storage API.
This model is the abstraction layer across all DB backends.
"""


class Model(object):
    """Base class for storage API models."""
    def __init__(self, **kwds):
        self.fields = list(kwds)
        for k, v in kwds.iteritems():
            setattr(self, k, v)

    def as_dict(self):
        d = {}
        for f in self.fields:
            v = getattr(self, f)
            if isinstance(v, Model):
                v = v.as_dict()
            elif isinstance(v, list) and v and isinstance(v[0], Model):
                v = [sub.as_dict() for sub in v]
            d[f] = v
        return d

    def __eq__(self, other):
        return self.as_dict() == other.as_dict()

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


class Account(Model):
    """The DB model of user

    :param user_id: The uuid of the user
    :param balance: The balance of the user
    :param consumption: The consumption of the
    :param currency: The currency of the user
    """
    def __init__(self,
                 user_id, domain_id, balance, consumption,
                 level, deleted=None, owed=None, created_at=None,
                 updated_at=None, deleted_at=None, owed_at=None,
                 *args, **kwargs):
        Model.__init__(
            self,
            user_id=user_id,
            domain_id=domain_id,
            balance=balance,
            consumption=consumption,
            level=level,
            deleted=deleted,
            owed=owed,
            owed_at=owed_at,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at)


class Charge(Model):
    """The charge record db model

    :param charge_id: The uuid of the charge
    :param user_id: The uuid of the user
    :param value: The charge value one time
    :param charge_time: The charge time
    """
    def __init__(self, charge_id, user_id, domain_id,
                 value, charge_time,
                 type=None, come_from=None, trading_number=None,
                 operator=None, remarks=None,
                 created_at=None, updated_at=None,
                 *args, **kwargs):
        Model.__init__(
            self,
            charge_id=charge_id,
            user_id=user_id,
            domain_id=domain_id,
            value=value,
            type=type,
            come_from=come_from,
            trading_number=trading_number,
            operator=operator,
            remarks=remarks,
            charge_time=charge_time,
            created_at=created_at,
            updated_at=updated_at)


class Project(Model):
    def __init__(self, user_id, project_id, domain_id, consumption,
                 created_at=None, updated_at=None, *args, **kwargs):
        Model.__init__(self,
                       user_id=user_id,
                       project_id=project_id,
                       domain_id=domain_id,
                       consumption=consumption,
                       created_at=created_at,
                       updated_at=updated_at)


class UsrPrjRelation(Model):
    def __init__(self, user_id, project_id, domain_id, consumption,
                 created_at=None, updated_at=None, *args, **kwargs):
        Model.__init__(self,
                       user_id=user_id,
                       project_id=project_id,
                       domain_id=domain_id,
                       consumption=consumption,
                       created_at=created_at,
                       updated_at=updated_at)
