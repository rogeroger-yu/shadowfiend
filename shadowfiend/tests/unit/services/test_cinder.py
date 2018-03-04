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

from cinderclient import client as cinder_client
from shadowfiend.services import cinder
from shadowfiend.tests.unit.db import base


mock_attachment = [
    {
        "id": "67e78d44-5337-4eb1-bae9-13a0dbe589b6",
        "device": "/dev/vdc",
        "volume_id": "67e78d44-5337-4eb1-bae9-13a0dbe589b6",
        "host_name": None,
        "attached_at": "2017-10-23T04:09:13.000000",
        "attachment_id": "9adf7e53-e625-4d99-b995-da1fa0f78d96",
        "server_id": "47d67731-8594-4021-bc08-c886068a53cf"
    }
]


def mock_client_init(self):
    self.cinder_client = cinder_client.Client(
        version='2',
        session=None,
        auth_url=None)


class Mock_Volume_Modle(object):
    def __init__(self, *args, **kwargs):
        self.id = '5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9'
        self.display_name = 'mock_volume'
        self.status = 'available'
        self.attachments = mock_attachment
        self.size = 1


class mock_cinder_client(object):
    def __init__(*args, **kwargs):
        pass

    class volume_snapshots(object):
        @staticmethod
        def list(*args, **kwargs):
            return ['0ddad27c-40b1-497d-923f-8041920343f5',
                    'd342782e-3fee-43ac-af8e-f0a0fdfce628']

        @staticmethod
        def delete(*args):
            pass

    class volumes(object):
        @staticmethod
        def get(*args, **kwargs):
            volume = Mock_Volume_Modle()
            return volume

        @staticmethod
        def detach(*args):
            pass

        @staticmethod
        def delete(*args):
            pass


class TestDropCinderResource(base.DbTestCase):
    def setUp(self):
        super(TestDropCinderResource, self).setUp()

        with mock.patch.object(
            cinder.CinderClient, '__init__', mock_client_init):
            with mock.patch.object(
                cinder_client, 'Client', mock_cinder_client):
                self.client = cinder.CinderClient()

    def test_get_volume(self):
        self.client.get_volume('5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9')

    def test_delete_volume(self):
        self.client.delete_volume('5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9')

    def test_delete_snapshot(self):
        self.client.delete_snapshot('1cbad27c-40b1-497d-923f-9041920343e5')

    def test_drop_resource(self):
        with mock.patch.object(
            cinder.CinderClient, '__init__', mock_client_init):
            with mock.patch.object(
                cinder_client, 'Client', mock_cinder_client):
                cinder.drop_resource('volume.volume',
                                     '5cb095ad-ada1-4e54-b4a0-bbdb0b54c5f9')
                cinder.drop_resource('volume.snapshot',
                                     '1cbad27c-40b1-497d-923f-9041920343e5')
