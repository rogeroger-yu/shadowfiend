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

from oslo_versionedobjects import base


class ShadowfiendObjectRegistry(base.VersionedObjectRegistry):
    pass


class ShadowfiendObject(base.VersionedObject):
    """Base class and object factory.

    This forms the base of all objects that can be remoted or instantiated
    via RPC. Simply defining a class that inherits from this base class
    will make it remotely instantiatable. Objects should implement the
    necessary "get" classmethod routines as well as "save" object methods
    as appropriate.
    """

    OBJ_SERIAL_NAMESPACE = 'shadowfiend_object'
    OBJ_PROJECT_NAMESPACE = 'shadowfiend'

    def as_dict(self):
        return {k: getattr(self, k)
                for k in self.fields
                if self.obj_attr_is_set(k)}


class ShadowfiendObjectSerializer(base.VersionedObjectSerializer):
    # Base class to use for object hydration
    OBJ_BASE_CLASS = ShadowfiendObject
