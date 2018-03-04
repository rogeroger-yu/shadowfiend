# Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import mock

from neutronclient.v2_0 import client as neutron_client
from shadowfiend.services import neutron
from shadowfiend.tests.unit.db import base


def mock_client_init(self):
    self.neutron_client = neutron_client.Client(
        version='2',
        session=None,
        auth_url=None)


class mock_neutron_client(object):
    def __init__(*args, **kwargs):
        pass

    def delete_loadbalancer(*args):
        pass

    def update_floatingip(*args):
        pass

    def delete_floatingip(*args):
        pass


class TestDropNeutronResource(base.DbTestCase):
    def setUp(self):
        super(TestDropNeutronResource, self).setUp()

        with mock.patch.object(
            neutron.NeutronClient, '__init__', mock_client_init):
            with mock.patch.object(
                neutron_client, 'Client', mock_neutron_client):
                self.client = neutron.NeutronClient()

    def test_delete_loadbalancer(self):
        self.client.delete_loadbalancer('5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9')

    def test_delete_fip(self):
        self.client.delete_fip('43b095ad-cda1-5e54-a4a0-abdb0b54c5f9')

    def test_drop_resource(self):
        with mock.patch.object(
            neutron_client, 'Client', mock_neutron_client):
            neutron.drop_resource('ratelimit.fip',
                                  '5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9')
            neutron.drop_resource('loadbalancer',
                                  '4ca045ac-cdb2-ee57-a4a0-abab0b54c5f8')
