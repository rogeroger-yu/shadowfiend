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

from novaclient import client as nova_client
from shadowfiend.services import nova
from shadowfiend.tests.unit.db import base


def mock_client_init(self):
    self.nova_client = nova_client.Client(
        version='2',
        session=None,
        auth_url=None)


class mock_nova_client(object):
    def __init__(self, *args, **kwargs):
        pass

    class servers(object):
        @staticmethod
        def delete(*args):
            pass


class TestDropNovaResource(base.DbTestCase):
    def setUp(self):
        super(TestDropNovaResource, self).setUp()

        with mock.patch.object(
            nova.NovaClient, '__init__', mock_client_init):
            with mock.patch.object(
                nova_client, 'Client', mock_nova_client):
                self.client = nova.NovaClient()

    def test_delete_server(self):
        self.client.delete_server('5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9')

    def test_drop_server(self):
        with mock.patch.object(
            nova.NovaClient, '__init__', mock_client_init):
            with mock.patch.object(
                nova_client, 'Client', mock_nova_client):
                nova.drop_resource('compute',
                                   '5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9')
