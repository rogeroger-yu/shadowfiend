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

from gnocchiclient import client as gnocchi_client
from shadowfiend.services import gnocchi
from shadowfiend.tests.unit.db import base


def mock_client_init(self):
    self.gnocchi_client = gnocchi_client.Client(
        version='2',
        session=None)


class mock_gnocchi_client(object):
    def __init__(*args, **kwargs):
        pass

    class archive_policy(object):
        @staticmethod
        def create(*args):
            pass

        @staticmethod
        def get(*args):
            pass

    class resource_type(object):
        @staticmethod
        def create(*args):
            pass


class TestDropGnocchiResource(base.DbTestCase):
    def setUp(self):
        super(TestDropGnocchiResource, self).setUp()

        with mock.patch.object(
            gnocchi.GnocchiClient, '__init__', mock_client_init):
            with mock.patch.object(
                gnocchi_client, 'Client', mock_gnocchi_client):
                self.client = gnocchi.GnocchiClient()

    def test_init_storage_backend(self):
        self.client.init_storage_backend()
