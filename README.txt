sockstomp
=========

setup
-----

```sh
user@host:dev/dir$ mkvirtualenv sockstomp
(sockstomp)user@host:dev/dir$ easy_install pyramid
(sockstomp)user@host:dev/dir$ pcreate -s alchemy sockstomp
(sockstomp)user@host:dev/dir$ cd sockstomp
(sockstomp)user@host:dev/dir/sockstomp$ python setup.py develop
(sockstomp)user@host:dev/dir/sockstomp$ initialize_sockstomp_db development.ini
(sockstomp)user@host:dev/dir/sockstomp$ pserve development.ini
```
the scaffold should be setup and running on [localhost:6543](http://localhost:6543).