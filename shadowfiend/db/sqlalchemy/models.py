"""
SQLAlchemy models for Shadowfiend data
"""

import json
import urlparse
from oslo_config import cfg

from sqlalchemy import Column, Integer, String
from sqlalchemy import DateTime, Index, DECIMAL, Boolean, Text
from sqlalchemy.types import TypeDecorator
from sqlalchemy.ext.declarative import declarative_base

from Shadowfiend.openstack.common import timeutils

sql_opts = [
    cfg.StrOpt('mysql_engine',
               default='InnoDB',
               help='MySQL engine')
]

cfg.CONF.register_opts(sql_opts)


def table_args():
    engine_name = urlparse.urlparse(cfg.CONF.database.connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': cfg.CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class ShadowfiendBase(object):
    """Base class for Shadowfiend Models."""
    __table_args__ = table_args()
    __table_initialized__ = False

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in values.iteritems():
            setattr(self, k, v)


Base = declarative_base(cls=ShadowfiendBase)


class Account(Base):

    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255))
    domain_id = Column(String(255))
    balance = Column(DECIMAL(20, 4))
    frozen_balance = Column(DECIMAL(20, 4), default=0)
    consumption = Column(DECIMAL(20, 4))
    level = Column(Integer)
    owed = Column(Boolean, default=False)
    deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=timeutils.utcnow)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)


class Project(Base):

    __tablename__ = 'project'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255))
    project_id = Column(String(255))
    consumption = Column(DECIMAL(20, 4))
    domain_id = Column(String(255))

    created_at = Column(DateTime, default=timeutils.utcnow)
    updated_at = Column(DateTime, default=timeutils.utcnow)


class UsrPrjRelation(Base):

    __tablename__ = 'user_project'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255))
    project_id = Column(String(255))
    consumption = Column(DECIMAL(20, 4))
    domain_id = Column(String(255))

    created_at = Column(DateTime, default=timeutils.utcnow)
    updated_at = Column(DateTime, default=timeutils.utcnow)


class Charge(Base):

    __tablename__ = 'charge'

    id = Column(Integer, primary_key=True)
    charge_id = Column(String(255))
    user_id = Column(String(255))
    domain_id = Column(String(255))
    value = Column(DECIMAL(20, 4))
    type = Column(String(64))
    come_from = Column(String(255))
    charge_time = Column(DateTime)
    trading_number = Column(String(255))
    operator = Column(String(64))
    remarks = Column(String(255))

    created_at = Column(DateTime, default=timeutils.utcnow)
    updated_at = Column(DateTime)
