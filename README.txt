# SockStomp

SockStomp is a pyramid plugin for the [stomp](https://stomp.github.io/) protocol using websockets as a means of transportation. The central idea is to create http requests from incoming stomp frames and inject them into pyramids view-system to benefit from its existing functionality (request-response cycle, permissions, predicates and other decorators). It also aims to provide access to user connections for push-messages.

Development was haltet to see where python 3 is going with [asyncio](https://docs.python.org/3/library/asyncio.html).

## Installation

### system dependencies

Depending on your distro keep either `postgresql-devel` (ubuntu) or `libpq-dev` (debian) in the below list.
```
sudo apt-get install \
  build-essential \
  libssl-dev \
  libffi-dev \
  python-dev \
  libevent-dev \
  python-pip \
  python-psycopg2 \
  postgresql-devel \
  libpq-dev
```

### virtualenv

Now that pip is installed
```
sudo pip install virtualenvwrapper
```
Edit your startup bash script `~/.profile` or `~/.bashrc` add the following lines to the end of the file:
```sh
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
```

Logout and log back in or manually source it via
```
source .profile # or .bashrc
```

### Project 
```sh
user@host:dev/dir$ mkvirtualenv sockstomp
(sockstomp) user@host:dev/dir$ easy_install pyramid
(sockstomp) user@host:dev/dir$ pip install pyramid_sockjs pyramid_jwtauth pyramid_dogpile_cache pyparsing
(sockstomp) user@host:dev/dir$ echo "gevent-websocket==0.3.6" > requirements.txt
(sockstomp) user@host:dev/dir$ pip install -r requirements.txt # fixed version
(sockstomp) user@host:dev/dir$ pcreate -s alchemy sockstomp
(sockstomp) user@host:dev/dir$ cd sockstomp
(sockstomp) user@host:dev/dir/sockstomp$ python setup.py develop
(sockstomp) user@host:dev/dir/sockstomp$ initialize_sockstomp_db development.ini
(sockstomp) user@host:dev/dir/sockstomp$ pserve --reload development.ini
```
the scaffold should be setup and running on [localhost:6543](http://localhost:6543).

### Database
SSH-tunnel to remote postgres database:
```
ssh -L 5432:127.0.0.1:5432 username@host
```

### Caching
```
sudo apt-get install memcached libmemcached-dev
memcached -d -m memory -s $HOME/memcached.sock -P $HOME/memcached.pid 
```

## Roadmap

- [ ] JWT - needs `libssl-dev` and `libffi-dev` [more][1]

[1]: http://stackoverflow.com/questions/22073516/failed-to-install-python-cryptography-package-with-pip-and-setup-py