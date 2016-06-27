# use python2.7.8
import os
import re
from datetime import datetime

from fabric.api import *

env.user = 'wsn'
env.sudo_user = 'root'

env.hosts = ['58.214.236.152']
env.port = 5622

db_user = 'www-data'
db_password = 'www-data'


###
# for build
###
_TAR_FILE = 'dist-awesome.tar.gz'


def build():
    includes = ['static', 'templates', 'config', '*.py', '*.sql']
    excludes = ['test', '.*', '*.pyc', '*.pyo', '*/__pycache__/']
    local('rm -f dist/%s' % _TAR_FILE)
    with lcd(os.path.join(os.path.abspath('.'), 'www')):
        cmd = ['tar', '--dereference', '-czvf', '../dist/%s' % _TAR_FILE]
        cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
        cmd.extend(includes)
        local(' '.join(cmd))


###
# for deploy
###
_REMOTE_TMP_TAR = '/tmp/%s' % _TAR_FILE
_REMOTE_BASE_DIR = '/srv/awesome'


def deploy():
    newdir = 'www-%s' % datetime.now().strftime('%y-%m-%d_%H.%M.%S')
    run('rm -f %s' % _REMOTE_TMP_TAR)
    put(('dist/%s' % _TAR_FILE), _REMOTE_TMP_TAR)
    with cd(_REMOTE_BASE_DIR):
        sudo('mkdir %s' % newdir)
    with cd('%s/%s' % (_REMOTE_BASE_DIR, newdir)):
        sudo('tar -zxvf %s' % _REMOTE_TMP_TAR)
    with cd(_REMOTE_BASE_DIR):
        sudo('rm -f www')
        sudo('ln -s %s www' % newdir)
        sudo('chown www-data:www-data www')
        sudo('chown -R www-data:www-data %s' % newdir)
    with settings(warn_only=True):
        # why add this command???
        sudo('supervisord')
        sudo('supervisorctl stop awesome')
        sudo('supervisorctl start awesome')
        sudo('/etc/init.d/nginx reload')
