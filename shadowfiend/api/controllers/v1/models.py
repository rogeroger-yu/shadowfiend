import datetime
from wsme import types as wtypes


class APIBase(wtypes.Base):
    def __init__(self, **kw):
        for key, value in kw.items():
            if isinstance(value, datetime.datetime):
                #kw[k] = timeutils.isotime(at=value)
                kw[key] = value
        super(APIBase, self).__init__(**kw)


class Version(APIBase):
    version = wtypes.text

class Test(APIBase):
    test_text = wtypes.text
