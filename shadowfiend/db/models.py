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


class Product(Model):
    """The DB Model, which should has the same fields with API models.

    :param product_id: UUID of the product
    :param name: The name of the product
    :param service: The service the product belongs to
    :param region_id: The region id the product belongs to
    :param description: Some description to this product
    :param type: The bill type of the product(regular/metered)
    :param deleted: If the product has been deleted
    :param unit_price: The unit price of the product
    """
    def __init__(self,
                 product_id, name, service, region_id, description,
                 deleted, unit_price, created_at=None, updated_at=None,
                 deleted_at=None, *args, **kwargs):
        Model.__init__(
            self,
            product_id=product_id,
            name=name,
            service=service,
            region_id=region_id,
            description=description,
            deleted=deleted,
            unit_price=unit_price,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at
        )


class Order(Model):
    """The DB Model for order

    :param order_id: UUID of the order
    :param resource_id: UUID of the resource
    :param resource_name: The name of the resource
    :param type: The type of the order
    :param status: The status of this subscription, maybe active, delete
    :param unit_price: The unit price of this order, add up active subs
    :param unit: The unit of this order
    :param total_price: The total fee this resource spent from creation to now
    :param cron_time: The next bill time
    :param date_time: The date time when the resource be deleted
    :param user_id: The user id this subscription belongs to
    :param project_id: The project id this subscription belongs to
    """
    def __init__(self,
                 order_id, resource_id, resource_name, type, status,
                 unit_price, unit, user_id, project_id, region_id,
                 total_price=None, cron_time=None, date_time=None,
                 domain_id=None, owed=None, renew=None, renew_method=None,
                 renew_period=None, charged=None, created_at=None,
                 updated_at=None, *args, **kwargs):
        Model.__init__(
            self,
            order_id=order_id,
            resource_id=resource_id,
            resource_name=resource_name,
            type=type,
            status=status,
            unit_price=unit_price,
            unit=unit,
            total_price=total_price,
            cron_time=cron_time,
            date_time=date_time,
            user_id=user_id,
            project_id=project_id,
            region_id=region_id,
            domain_id=domain_id,
            owed=owed,
            charged=charged,
            renew=renew,
            renew_method=renew_method,
            renew_period=renew_period,
            created_at=created_at,
            updated_at=updated_at)


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
                 updated_at=None, deleted_at=None, *args, **kwargs):
        Model.__init__(
            self,
            user_id=user_id,
            domain_id=domain_id,
            balance=balance,
            consumption=consumption,
            level=level,
            deleted=deleted,
            owed=owed,
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
    def __init__(self, user_id, project_id, user_consumption,
                 project_consumption, is_historical,
                 created_at, *args, **kwargs):
        Model.__init__(self,
                       user_id=user_id,
                       project_id=project_id,
                       user_consumption=user_consumption,
                       project_consumption=project_consumption,
                       is_historical=is_historical,
                       created_at=created_at)
