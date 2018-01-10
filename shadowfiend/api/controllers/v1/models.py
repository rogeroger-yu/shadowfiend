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

import datetime
import wsme
from wsme import types as wtypes


class APIBase(wtypes.Base):
    def __init__(self, **kw):
        for key, value in kw.items():
            if isinstance(value, datetime.datetime):
                # kw[k] = timeutils.isotime(at=value)
                kw[key] = value
        super(APIBase, self).__init__(**kw)

    @classmethod
    def from_db_model(cls, m):
        return cls(**(m))

    @classmethod
    def transform(cls, **kwargs):
        return cls(**kwargs)

    def as_dict(self):
        return dict((k.name, getattr(self, k.name))
                    for k in wtypes.inspect_class(self.__class__)
                    if getattr(self, k.name) != wsme.Unset)


class Version(APIBase):
    version = wtypes.text


class Summary(APIBase):
    """Summary of one single kind of order."""
    total_price = float
    total_count = int
    order_type = wtypes.text


class Summaries(APIBase):
    """Summary of all kind of orders."""
    total_price = float
    total_count = int
    summaries = [Summary]


class AdminAccount(APIBase):
    """Account Detail for a tenant"""
    balance = float
    consumption = float
    level = int
    user_id = wtypes.text
    project_id = wtypes.text
    domain_id = wtypes.text
    sales_id = wtypes.text
    owed = bool
    inviter = wtypes.text
    created_at = wtypes.text
    update_at = wtypes.text


class AdminAccounts(APIBase):
    total_count = int
    accounts = [AdminAccount]


class User(APIBase):
    """UOS user model."""
    user_id = wtypes.text
    user_name = wtypes.text
    email = wtypes.text
    real_name = wtypes.text
    mobile = wtypes.text
    company = wtypes.text


class UserAccount(APIBase):
    balance = float
    consumption = float
    owed = bool
    level = int


class Project(APIBase):
    user_id = wtypes.text
    project_id = wtypes.text
    domain_id = wtypes.text
    consumption = float
    created_at = wtypes.text


class UserProject(APIBase):
    user_id = wtypes.text
    project_id = wtypes.text
    domain_id = wtypes.text
    project_name = wtypes.text
    user_consumption = float
    project_consumption = float
    billing_owner = {wtypes.text: wtypes.text}
    project_owner = {wtypes.text: wtypes.text}
    project_creator = {wtypes.text: wtypes.text}
    is_historical = bool
    created_at = wtypes.text


class Charge(APIBase):
    """Charge to account."""
    charge_id = wtypes.text
    value = float
    type = wtypes.text
    come_from = wtypes.text
    trading_number = wtypes.text
    charge_time = wtypes.text
    target = User
    actor = User
    remarks = wtypes.text


class Charges(APIBase):
    total_price = float
    total_count = int
    charges = [Charge]


class TransferMoneyBody(APIBase):
    user_id_to = wtypes.text
    user_id_from = wtypes.text
    money = float
    remarks = wtypes.text


class Estimate(APIBase):
    balance = float
    price_per_hour = float
    remaining_day = int


class BalanceFrozenResult(APIBase):
    user_id = wtypes.text
    project_id = wtypes.text
    balance = float


class BalanceFrozenBody(APIBase):
    total_price = wsme.wsattr(float, mandatory=True)


class OrderPostBody(APIBase):
    """One single order."""
    order_id = wtypes.text
    unit_price = float
    unit = wtypes.text
    period = int
    renew = bool
    resource_id = wtypes.text
    resource_name = wtypes.text
    user_id = wtypes.text
    project_id = wtypes.text
    region_id = wtypes.text
    type = wtypes.text
    status = wtypes.text


class OrderPutBody(APIBase):
    order_id = wtypes.text
    change_to = wtypes.text
    cron_time = wtypes.text
    change_order_status = bool
    first_change_to = wtypes.text


class Order(APIBase):
    """One single order."""
    order_id = wtypes.text
    resource_id = wtypes.text
    resource_name = wtypes.text
    status = wtypes.text
    unit_price = float
    unit = wtypes.text
    total_price = float
    type = wtypes.text
    cron_time = wtypes.text
    date_time = wtypes.text
    created_at = wtypes.text
    updated_at = wtypes.text
    user_id = wtypes.text
    project_id = wtypes.text
    domain_id = wtypes.text
    region_id = wtypes.text
    owed = bool
    renew = bool
    renew_method = wtypes.text
    renew_period = int


class Orders(APIBase):
    """Collection of orders."""
    total_count = int
    orders = [Order]
