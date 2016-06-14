# -*- coding: utf-8 -*-
# /**
#  * @brief       :
#  * @file        : handlers.py
#  * @version     : v0.0.1
#  * @author      : gang.cheng
#  * @date        : 2016-06-10
#  * change logs  :
#  * Date       Version     Author        Note
#  * 2016-06-10  v0.0.1  gang.cheng    first version
#  */

__author__ = 'gang.cheng'

' url handlers '

import time
import json
import logging
import hashlib
import base64
import asyncio

from coroweb import get, post
from models import User, Comment, Blog, next_id


@get('/')
@asyncio.coroutine
def index(request):
    users = yield from User.find_all()
    return {
        '__template__': 'test.html',
        'users': users
    }

