
import os
import unittest

from pyramid import testing
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

from mock import Mock
from webtest import TestApp

from sockstomp import main
from sockstomp.models import Base

# get settings
# ------------

here = os.path.dirname(__file__)
config_uri = os.path.join(here, '../../', 'development.ini')

setup_logging(config_uri)
settings = get_appsettings(config_uri)

# test definitions
# ----------------

class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = engine_from_config(settings, prefix='sqlalchemy.')
        cls.engine.pool._use_threadlocal = True
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        connection = self.engine.connect()

        # begin a non-ORM transaction
        self.trans = connection.begin()

        # bind an individual Session to the connection
        self.Session.configure(bind=connection)
        self.session = self.Session(bind=connection)
        Base.session = self.session


class UnitTestBase(BaseTestCase):
    def setUp(self):
        self.config = testing.setUp(request=testing.DummyRequest())
        super(UnitTestBase, self).setUp()


class IntegrationTestBase(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = main({}, **settings)
        super(IntegrationTestBase, cls).setUpClass()

    def setUp(self):
        self.app = TestApp(self.app)
        self.config = testing.setUp()
        super(IntegrationTestBase, self).setUp()