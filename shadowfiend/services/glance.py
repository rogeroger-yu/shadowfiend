import functools
import logging as log

from glanceclient import client as glance_client
from glanceclient.exc import NotFound,HTTPNotFound

from shadowfiend.common import utils
from shadowfiend.common import timeutils
from shadowfiend.common import constants as const
from shadowfiend.services import keystone as ks_client
from shadowfiend.services import BaseClient
from shadowfiend.services import Resource


LOG = log.getLogger(__name__)


class GlanceClient(BaseClient):
    def __init__(self):
        super(GlanceClient, self).__init__()

        self.glance_client = glance_client.Client(
            version='1',
            session=self.session,
            auth=self.auth)

    def image_get(self, image_id, region_name=None):
        try:
            image = self.glance_client.images.get(image_id)
        except HTTPNotFound:
            return None
        except NotFound:
            return None
        status = utils.transform_status(image.status)
        return Image(id=image.id,
                     name=image.name,
                     image_label=image.get('image_label', 'default').lower(),
                     status=status,
                     original_status=image.status,
                     resource_type=const.RESOURCE_IMAGE,
                     size=image.size)
 
    def image_list(self, project_id, region_name=None, project_name=None):
        filters = {'owner': project_id}
        images = self.glance_client.images.list(filters=filters)
        formatted_images = []
        for image in images:
            created_at = utils.format_datetime(image.created_at)
            status = utils.transform_status(image.status)
            formatted_images.append(Image(id=image.id,
                                          name=getattr(image, 'name', None),
                                          size=getattr(image, 'size', 0),
                                          status=status,
                                          original_status=image.status,
                                          resource_type=const.RESOURCE_IMAGE,
                                          project_id=project_id,
                                          project_name=project_name,
                                          created_at=created_at))
        return formatted_images
 
    def delete_images(self, project_id, region_name=None):
        filters = {'owner': project_id}
        images = self.glance_client.images.list(filters=filters)
        for image in images:
            self.glance_client.images.delete(image.id)
            LOG.warn("Delete image: %s" % image.id)
 
    def delete_image(self, image_id, region_name=None):
        self.glance_client.images.delete(image_id)
 
    def stop_image(self, image_id, region_name):
        return True
 

class Image(Resource):
    def to_message(self):
        msg = {
            'event_type': 'image.activate.again',
            'payload': {
                'id': self.id,
                'name': self.name,
                'size': self.size,
                'owner': self.project_id,
            },
            'timestamp': utils.format_datetime(timeutils.strtime())
        }
        return msg

    def to_env(self):
        return dict(HTTP_X_USER_ID=None,
                    HTTP_X_PROJECT_ID=self.project_id,
                    HTTP_X_IMAGE_META_PROPERTY_BASE_IMAGE_REF=self.id)

    def to_body(self):
        return {}
