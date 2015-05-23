sockstomp
=========

setup
-----

depending on your distro keep either `postgresql-devel` (ubuntu) or
`libpq-dev` (debian) in the below list.
```
sudo apt-get install build-essential libssl-dev libffi-dev python-dev\
  libevent-dev python-pip python-psycopg2 postgresql-devel libpq-dev
```
now that pip is installed
```
sudo pip install virtualenvwrapper
```
and edit your startup bash script `~/.profile` or `~/.bashrc` add the
following lines to the end of the file:
```sh
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
```
logout and log back in or manually source it via
```
source .profile # or .bashrc
```
project setup:
```sh
user@host:dev/dir$ mkvirtualenv sockstomp
(sockstomp)user@host:dev/dir$ easy_install pyramid
(sockstomp)user@host:dev/dir$ pip install pyramid_sockjs pyramid_jwtauth pyparsing
(sockstomp)user@host:dev/dir$ echo "gevent-websocket==0.3.6" > requirements.txt
(sockstomp)user@host:dev/dir$ pip install -r requirements.txt # fixed version
(sockstomp)user@host:dev/dir$ pcreate -s alchemy sockstomp
(sockstomp)user@host:dev/dir$ cd sockstomp
(sockstomp)user@host:dev/dir/sockstomp$ python setup.py develop
(sockstomp)user@host:dev/dir/sockstomp$ initialize_sockstomp_db development.ini
(sockstomp)user@host:dev/dir/sockstomp$ pserve --reload development.ini
```
the scaffold should be setup and running on [localhost:6543](http://localhost:6543).
