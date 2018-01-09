#!/usr/bin/env python
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

import logging as log
import requests

from oslo_config import cfg

from shadowfiend.common import exception
from shadowfiend.services import keystone
from shadowfiend.services import wrap_exception

LOG = log.getLogger(__name__)


@wrap_exception(exc_type='get', with_raise=False)
def get_uos_user(user_id):
    # NOTE(chengkun): Now The user's detail info is stored in kunkka,
    # so we should use kunkka api to get user info.
    ks_client = keystone.KeystoneClient()
    ks_cfg = cfg.CONF.keystone_authtoken
    auth_url = '%s://%s' % (ks_cfg.auth_protocol, ks_cfg.auth_host)
    url = auth_url + '/api/v1/user/%s' % user_id
    r = requests.get(url,
                     headers={'Content-Type': 'application/json',
                              'X-Auth-Token': ks_client.get_token()})
    if r.status_code == 404:
        LOG.warn("can't not find user %s from kunkka" % user_id)
        raise exception.NotFound()
    return r.json()
