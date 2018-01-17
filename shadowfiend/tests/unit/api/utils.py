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
"""
Utils for testing the API service.
"""

from shadowfiend.tests.unit.db import utils


def account_post_data(**kwargs):
    account = utils.get_test_account(**kwargs)
    return account


def account_put_charge_data(**kwargs):
    data = {'value': 10}
    return data


def account_put_level_data(**kwargs):
    data = {'level': 5}
    return data
