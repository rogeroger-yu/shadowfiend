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
import json
import pecan
import tablib

from pecan import rest
from pecan import response

from wsmeext.pecan import wsexpose
from wsme import types as wtypes

from oslo_log import log

from shadowfiend.common import exception
from shadowfiend.common import policy
from shadowfiend.api import acl
from shadowfiend.api.controllers.v1 import models
from shadowfiend.processor.service import fetcher
from shadowfiend.services import keystone as ks_client
from shadowfiend.common import timeutils


LOG = log.getLogger(__name__)
HOOK = pecan.request


class ChargesController(rest.RestController):

    @wsexpose(None, wtypes.text, wtypes.text, datetime.datetime,
              datetime.datetime, int, int, bool, status=204)
    def get(self, output_format='xlsx', user_id=None,
            start_time=None, end_time=None,
            limit=None, offset=None, all_get=False):
        """Export all charges of special user, output formats supported:
           * Excel (Sets + Books)
           * YAML (Sets + Books)
           * HTML (Sets)
           * TSV (Sets)
           * CSV (Sets)
           * JSON (Sets)
        """
        policy.check_policy(HOOK.context, "charges:export",
                            action="charges:export")

        tablib.formats.json.json = json

        if output_format.lower() not in ["xls", "xlsx", "csv", "yaml", "json"]:
            raise exception.InvalidOutputFormat(output_format=output_format)

        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")
        if offset and offset < 0:
            raise exception.InvalidParameterValue(err="Invalid offset")

        policy.check_policy(HOOK.context, "charges:export",
                            action="charges:export")

        if all_get and acl.context_is_admin(HOOK.headers):
            user_id = None

        headers = (u"充值记录ID", u"充值对象用户名", u"充值对象ID",
                   u"充值对象邮箱", u"充值金额", u"充值类型",
                   u"充值来源", u"充值人员ID",
                   u"充值人员用户名", u"充值时间", u"状态")
        data = []

        users = {}

        def _get_user(user_id):
            if not user_id:
                return models.User(user_id=None,
                                   user_name=None,
                                   email=None)
            user = users.get(user_id)
            if user:
                return user
            contact = ks_client.get_user(user_id) or {}
            user_name = contact.get('name')
            email = contact.get('email')
            users[user_id] = models.User(user_id=user_id,
                                         user_name=user_name,
                                         email=email)
            return users[user_id]

        charges = HOOK.conductor_rpcapi.get_charges(
            HOOK.context,
            user_id=user_id,
            limit=limit,
            offset=offset,
            start_time=start_time,
            end_time=end_time)
        for charge in charges:
            charge_st = timeutils.str2ts(charge['charge_time']) + (3600 * 8)
            charge['charge_time'] = timeutils.ts2str(charge_st)
            acharge = models.Charge.from_db_model(charge)
            acharge.actor = _get_user(charge['operator'])
            acharge.target = _get_user(charge['user_id'])
            charge_time = charge['charge_time']

            adata = (acharge.charge_id, acharge.target.user_name,
                     acharge.target.user_id, acharge.target.email,
                     str(acharge.value), acharge.type, acharge.come_from,
                     acharge.actor.user_id, acharge.actor.user_name,
                     charge_time, u"正常")
            data.append(adata)

        data = tablib.Dataset(*data, headers=headers)

        response.content_type = "application/binary; charset=UTF-8"
        response.content_disposition = \
            "attachment; filename=charges.%s" % output_format
        # content = getattr(data, output_format)
        content = data.export(output_format)
        response.write(content)
        return response


class OrdersController(rest.RestController):
    """Report orders logic
    """
    @wsexpose(None, wtypes.text, wtypes.text, wtypes.text,
              datetime.datetime, datetime.datetime, int, int,
              wtypes.text, wtypes.text, bool, bool)
    def get_all(self, output_format='xlsx', type=None, status=None,
                start_time=None, end_time=None, limit=None, marker=None,
                project_id=None, user_id=None, owed=None,
                all_get=False):
        """Get queried orders
        If start_time and end_time is not None, will get orders that have bills
        during start_time and end_time, or return all orders directly.
        """
        policy.check_policy(HOOK.context, "charges:export",
                            action="charges:export")

        tablib.formats.json.json = json
        _gnocchi_fetcher = fetcher.GnocchiFetcher()

        if limit and limit < 0:
            raise exception.InvalidParameterValue(err="Invalid limit")

        policy.check_policy(HOOK.context, "charges:export",
                            action="charges:export")

        if all_get and acl.context_is_admin(HOOK.headers):
            user_id = None

        MAP = {"instance": u"虚拟机",
               "volume": u"云硬盘",
               "image": u"镜像",
               "ratelimit": u"限速",
               "network_lbaas_loadbalancer": u"负载均衡"}

        headers = (u"资源ID", u"资源名称", u"资源类型",
                   u"金额(元)", u"用户ID", u"项目ID",
                   u"创建时间")
        data = []

        adata = (u"过滤条件: 资源类型: %s, 用户ID: %s, "
                 u"项目ID: %s, 起始时间: %s, 结束时间: %s" %
                 (type, user_id, project_id,
                  start_time, end_time),
                 "", "", "", "", "", "")
        data.append(adata)

        resources = []

        for service in MAP:
            resources += _gnocchi_fetcher.get_resources(project_id, service)

        for resource in resources:
            if 'total.cost' in resource['metrics']:
                price = _gnocchi_fetcher.get_resource_price(
                    resource['metrics']['total.cost'], start_time, end_time)
                adata = (resource['id'], resource['display_name'],
                         MAP[resource['type']], price,
                         resource['user_id'], resource['project_id'],
                         resource['started_at'])
                data.append(adata)

        data = tablib.Dataset(*data, headers=headers)

        response.content_type = "application/binary; charset=UTF-8"
        response.content_disposition = \
            "attachment; filename=orders.%s" % output_format
        content = getattr(data, output_format)
        response.write(content)
        return response


class ReportsController(rest.RestController):
    """Manages operations on the reports operations
    """
    charges = ChargesController()
    orders = OrdersController()
