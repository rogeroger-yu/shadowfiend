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

from decimal import Decimal
from decimal import ROUND_HALF_UP
from shadowfiend.common import constants as const

import datetime
import six
import uuid

STATE_MAPPING = {
    'ACTIVE': const.STATE_RUNNING,
    'active': const.STATE_RUNNING,
    'available': const.STATE_RUNNING,
    'in-use': const.STATE_RUNNING,
    'deprecated': const.STATE_RUNNING,
    'DOWN': const.STATE_RUNNING,
    'SHUTOFF': const.STATE_STOPPED,
    'SUSPENDED': const.STATE_SUSPEND,
    'PAUSED': const.STATE_SUSPEND,
    'True': const.STATE_RUNNING,
    'False': const.STATE_STOPPED,
    'true': const.STATE_RUNNING,
    'false': const.STATE_STOPPED,
}


def _quantize_decimal(value):
    if isinstance(value, Decimal):
        return value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(Decimal('0.0001'),
                                        rounding=ROUND_HALF_UP)


def transform_status(status):
    try:
        return STATE_MAPPING[status]
    except KeyError:
        return const.STATE_ERROR


def format_datetime(dt):
    return '%s %s.000000' % (dt[:10], dt[11:19])


def true_or_false(abool):
    if isinstance(abool, bool):
        return abool
    elif isinstance(abool, six.string_types):
        abool = abool.lower()
        if abool == 'true':
            return True
        if abool == 'false':
            return False
    raise ValueError("should be bool or true/false string")


def normalize_timedelta(duration):
    if not duration:
        return
    unit = duration[-1]
    value = duration[:-1]
    if unit == 'm':
        return datetime.timedelta(minutes=float(value))
    if unit == 'h':
        return datetime.timedelta(hours=float(value))
    if unit == 'd':
        return datetime.timedelta(days=float(value))
    raise ValueError("unsupport time unit")


def is_uuid_like(val):
    """Returns validation of a value as a UUID.

    For our purposes, a UUID is a canonical form string:
    aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa

    """
    try:
        return str(uuid.UUID(val)) == val
    except (TypeError, ValueError, AttributeError):
        return False
