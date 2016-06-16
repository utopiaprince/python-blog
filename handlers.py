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

import re
import time
import json
import logging
import hashlib
import base64
import asyncio

from coroweb import get, post
from models import User, Comment, Blog, next_id

from apis import APIValueError, APIResourceNotFoundError

from config.config import configs


@get('/')
@asyncio.coroutine
def index(request):
    # users = yield from User.find_all()
    # return {
    #     '__template__': 'test.html',
    #     'users': users
    # }
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary,
             created_at=time.time() - 120),
        Blog(id='2', name='Something New',
             summary=summary, created_at=time.time() - 3600),
        Blog(id='3', name='Learn Swift', summary=summary,
             created_at=time.time() - 7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }


@get('/api/users')
def api_get_users(*, page='1'):
    # page_index = get_page_index(page)
    # num = yield from User.find_num('count(id)')
    # p = Page(num, page_index)
    # if num == 0:
    #     return dict(page=p, users=())
    # users = yield from User.find_all(orderBy='created_at desc', limit=(p.offset, p.limit))
    users = yield from User.find_all(orderBy='created_at desc')
    for u in users:
        u.passwd = '******'
    # return dict(page=p, users=users)
    return dict(users=users)
