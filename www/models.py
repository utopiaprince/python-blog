# /**
#  * @brief       : this
#  * @file        : model.py
#  * @version     : v0.0.1
#  * @author      : gang.cheng
#  * @date        : 2015-06-06
#  * change logs  :
#  * Date       Version     Author        Note
#  * 2015-06-06  v0.0.1  gang.cheng    first version
#  */
import logging
import time
import uuid
import hashlib
import asyncio
from orm import Model, StringField, BooleanField, FloatField, TextField

from config.config import configs
COOKIE_KEY = configs.session.secret

def next_id():
    '''
    byte(15+2+32+3)=52 > 50
    alter table users modify id varchar(60);  修改数据库的数据类型
    '''
    return '%015d:%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

# print(next_id())


class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(60)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)

    @asyncio.coroutine
    def register(self):
        self.id = next_id()
        sha1_passwd = '%s:%s' %(self.id, self.passwd)
        self.passwd = hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest()
        yield from self.save()


    # 用户id＋过期时间＋sha1(用户id＋用户口令＋过期时间＋secretkey)
    #
    def user2cookie(self, max_age):
        expires = str(int(time.time() + max_age))
        s = '%s-%s-%s-%s' % (self.id, self.passwd, expires, COOKIE_KEY)
        L = [self.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
        return '-'.join(L)


    @classmethod
    async def cookie2user(cls, cookie_str):
        '''
        Parse cookie and load user if cookie is valid.
        xxxx--xxxxxx-bbbbbbb-ddddddddddddd
        '''
        if not cookie_str:
            return None
        try:
            L = cookie_str.split('-')
            if len(L) != 3:
                return None
            uid, expires, sha1 = L
            if int(expires) < time.time():
                return None
            user = await cls.find(uid)
            if user is None:
                return None
            s = '%s-%s-%s-%s' % (uid, user.passwd, expires, COOKIE_KEY)
            if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
                logging.info('invalid sha1')
                return None
            user.passwd = '******'
            return user
        except Exception as e:
            logging.exception(e)
            return None



class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(60)')
    user_id = StringField(ddl='varchar(60)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200')
    content = TextField()
    created_at = FloatField(default=time.time)


class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(60)')
    blog_id = StringField(ddl='varchar(60)')
    user_id = StringField(ddl='varchar(60)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)
