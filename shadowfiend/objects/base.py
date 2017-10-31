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

    OBJ_SERIAL_NAMESPACE = 'Shadowfiend_object'
    OBJ_PROJECT_NAMESPACE = 'Shadowfiend'

    def as_dict(self):
        return {k: getattr(self, k)
                for k in self.fields
                if self.obj_attr_is_set(k)}


class ShadowfiendObjectSerializer(base.VersionedObjectSerializer):
    # Base class to use for object hydration
    OBJ_BASE_CLASS = ShadowfiendObject
