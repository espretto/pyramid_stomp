
import os
import hashlib

from sqlalchemy import (
  Column,
  Integer,
  Unicode,
  Sequence,
  ForeignKey,
  Table,
  PickleType
  )
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON

# sqlalchemy essentials
# ---------------------
# create a base class for our orm models, giving them the power
# to persist themselves in the db.
# 
# http://docs.sqlalchemy.org/ru/latest/orm/tutorial.html#declare-a-mapping
Base = declarative_base()


def find_groups(userid, request):
    """finds a users groups

    serves pyramid's auth mechanism and finds a user's groups
    based on the userid to extend the principals returned by
    http://docs.pylonsproject.org/projects/pyramid/en/latest/_modules/pyramid/interfaces.html#IAuthenticationPolicy
    """
    user = User.by_id(request.db, userid)
    return ['g:%s' % group.name for group in user.groups]


class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)

    def __init__(self, name):
        self.name = name


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(Unicode(80), nullable=False, unique=True)
    password = Column(Unicode(80), nullable=True)
    groups = relationship(Group, secondary='assoc_user_group', backref='users')

    # velruse specific
    provider_id = Column(Integer)
    provider_name = Column(Unicode(80))
    provider_type = Column(Unicode(80))
    provider_profile = Column(PickleType)
    provider_credentials = Column(PickleType)

    def __init__(self, username, password, **kw):
        self.username = username
        self._set_password(password)
        self.provider_id = kw.get('provider_id')
        self.provider_name = kw.get('provider_name')
        self.provider_type = kw.get('provider_type')
        self.provider_profile = kw.get('profile')
        self.provider_credentials = kw.get('credentials')

    @classmethod
    def by_id(cls, db, userid):
        return db.query(User).filter(User.id==userid).first()

    @classmethod
    def by_username(cls, db, username):
        return db.query(User).filter(User.username==username).first()

    def _set_password(self, password):
        hashed_password = password

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password

        salt = hashlib.sha1()
        salt.update(os.urandom(60))
        hash = hashlib.sha1()
        hash.update(password_8bit + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()

        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        self.password = hashed_password

    def validate_password(self, password):
        hashed_pass = hashlib.sha1()
        hashed_pass.update(password + self.password[:40])
        return self.password[40:] == hashed_pass.hexdigest()

assoc_user_group_table = Table('assoc_user_group', Base.metadata,
    Column('user_id', Integer, ForeignKey(User.id)),
    Column('group_id', Integer, ForeignKey(Group.id)),
)