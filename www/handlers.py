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

import markdown2

from pygments import highlight
from pygments.lexers import Python3Lexer
from pygments.formatters import HtmlFormatter
from aiohttp import web

from coroweb import get, post
from apis import APIValueError, APIResourceNotFoundError, APIError, Page

from models import User, Comment, Blog, next_id

from config.config import configs
COOKIE_NAME = configs.session.name


def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()


def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), 
        filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)


def markdown_highlight(content):
    return re.sub(r'<pre><code>(?P<code>.+?)</code></pre>',
                  lambda m: highlight(
                      m.group('code'), Python3Lexer(), HtmlFormatter()),
                  markdown2.markdown(content), flags=re.S)


@get('/')
def index(*, page='1'):
    page_index = Page.get_index(page)
    num = yield from Blog.find_num('count(id)')
    page = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = yield from Blog.find_all(orderBy='created_at desc',
                                         limit=(page.offset, page.limit))
    for blog in blogs:
        # blog.summary = markdown_highlight(blog.summary)
        blog.html_content = markdown_highlight(blog.content)
    return {
        '__template__': 'bootstrap-blogs.html',
        'page': page,
        'blogs': blogs
    }


@get('/404')
def not_found():
    return {
        '__template__': '404.html'
    }


@get('/register')
def register():
    return {
        '__template__': 'bootstrap-register.html'
    }


@get('/signin')
def signin():
    return {
        '__template__': 'bootstrap-signin.html'
    }


@post('/api/authenticate')
def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = yield from User.find_all('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user.user2cookie(86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r


@get('/manage/')
def manage():
    return 'redirect:/manage/blogs'


@get('/manage/comments')
def manage_comments(*, page='1'):
    return {
        '__template__': 'manage_comments.html',
        'page_index': Page.get_index(page)
    }


@get('/manage/users')
def manage_users(*, page='1'):
    return {
        '__template__': 'manage_users.html',
        'page_index': Page.get_index(page)
    }


@get('/manage/blogs')
def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': Page.get_index(page)
    }


@get('/manage/blogs/create')
def manage_create_blog():
    logging.info('manage create blog () handler.')
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }


@get('/manage/blogs/edit')
def manage_edit_blog(*, id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs/%s' % id
    }

'''
this is for api/comments
'''


@get('/api/comments')
def api_comments(*, page='1'):
    page_index = Page.get_index(page)
    num = yield from Comment.find_num('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = yield from Comment.find_all(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)


@post('/api/blogs/{id}/comments')
def api_create_comment(id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = yield from Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id=blog.id, user_id=user.id,
                      user_name=user.name, user_image=user.image, content=content.strip())
    yield from comment.save()
    return comment


@post('/api/comments/{id}/delete')
def api_delete_comments(id, request):
    check_admin(request)
    c = yield from Comment.find(id)
    if c is None:
        raise APIResourceNotFoundError('Comment')
    yield from c.remove()
    return dict(id=id)

'''
this is for api/users
'''


@get('/api/users')
def api_get_users(*, page='1'):
    page_index = Page.get_index(page)
    num = yield from User.find_num('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = yield from User.find_all(orderBy='created_at desc', limit=(p.offset, p.limit))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)


_RE_EMAIL = re.compile(
    r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


@post('/api/users')
def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = yield from User.find_all('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    user = User(name=name.strip(), email=email, passwd=passwd,
                image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    yield from user.register()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user.user2cookie(86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

'''
this is for api/blogs
'''


@get('/api/blogs')
def api_blogs(*, page='1'):
    page_index = Page.get_index(page)
    num = yield from Blog.find_num('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = yield from Blog.find_all(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)


@post('/api/blogs')
def api_create_blog(request, *, name, summary, content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name,
                user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
    yield from blog.save()
    return blog


@get('/api/blogs/{id}')
def api_get_blog(*, id):
    blog = yield from Blog.find(id)
    return blog


@post('/api/blogs/{id}')
def api_update_blog(id, request, *, name, summary, content):
    check_admin(request)
    blog = yield from Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    yield from blog.update()
    return blog


@post('/api/blogs/{id}/delete')
def api_delete_blog(request, *, id):
    check_admin(request)
    blog = yield from Blog.find(id)
    yield from blog.remove()
    comments = yield from Comment.find_all('blog_id=?', [id])
    for c in comments:
        yield from c.remove()
    return dict(id=id)


@get('/blog/{id}')
def get_blog(id):
    blog = yield from Blog.find(id)
    comments = yield from Comment.find_all('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown_highlight(blog.content)
    return {
        '__template__': 'bootstrap-blog.html',
        'blog': blog,
        'comments': comments
    }
