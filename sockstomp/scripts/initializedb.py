import os
import sys
import transaction

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from pyramid.scripts.common import parse_vars
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from sockstomp.models import (
    Base,
    User,
    Group,
    )

def create_fixtures(session):
    admin_user = User('admin', 'admin')
    staff_user = User('staff', 'staff')
    guest_user = User('guest', 'guest')

    admin_group = Group('admin')
    staff_group = Group('staff')
    guest_group = Group('guest')

    session.add_all([admin_group, staff_group, guest_group])

    admin_user.groups.extend([admin_group, staff_group, guest_group])
    staff_user.groups.extend([staff_group, guest_group])
    guest_user.groups.append(guest_group)

    session.add_all([admin_user, staff_user, guest_user])

    session.commit()


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [drop|create|reset] [var=value]\n'
          '(example: "%s development.ini create")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 3:
        usage(argv)

    # parse command line arguments
    config_uri = argv[1]
    mode = argv[2]
    options = parse_vars(argv[3:])

    # apply settings
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)
    engine = engine_from_config(settings, 'sqlalchemy.')

    if mode == 'create':
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        create_fixtures(session);
    elif mode == 'drop':
        Base.metadata.drop_all(engine)
    elif mode == 'reset':
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        create_fixtures(session);
    else:
        usage(argv)