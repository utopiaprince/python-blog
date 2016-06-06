# /**
#  * @brief       : this
#  * @file        : orm.py
#  * @version     : v0.0.1
#  * @author      : gang.cheng(utopiaprince@qq.com)
#  * @date        : 2016-06-01
#  * change logs  :
#  * Date       Version     Author        Note
#  * 2015-06-01  v0.0.1  gang.cheng    first version
#  */
import asyncio
import logging
import aiomysql

# @asyncio.coroutine <--> yield from
# async <--> await


def log(sql, args=None):
    logging.info('SQL: [%s] args:%s' % (sql, str(args or [])))


@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )


@asyncio.coroutine
def close_pool():
    logging.info('close database connection pool...')
    global __pool
    __pool.close()
    yield from __pool.wait_closed()


# Select
@asyncio.coroutine
def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (yield from __pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs


# Insert, Update, Delete
@asyncio.coroutine
def execute(sql, args):
    log(sql, args)
    with (yield from __pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected


def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)


class ModeMetaClass(type):

    def __new__(cls, name, bases, attrs):
        # 排除Model类本身:
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # get table name:
        table_name = attrs.get('__table__', None) or name
        logging.info('found mdel: %s (table: %s)' % (name, table_name))
        # get all field and primary_key
        mappings = dict()
        fields = []
        pm_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('    found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if pm_key:
                        raise RuntimeError(
                            'Duplicate primary key for field: %s' % k)
                    pm_key = k
                else:
                    fields.append(k)
        if not pm_key:
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = table_name
        attrs['__pm_key__'] = pm_key
        attrs['__fields__'] = fields

        attrs['__select__'] = 'select`%s`, %s from `%s`' % (
            pm_key, ', '.join(escaped_fields), table_name)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
            table_name, ', '.join(escaped_fields), pm_key,
            create_args_string(len(escaped_fields) + 1))

        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
            table_name,
            ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)),
            pm_key)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (
            table_name, pm_key)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModeMetaClass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def get_value(self, key):
        return getattr(self, key, None)

    def get_value_or_def(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(
                    field.default) else field.default
                logging.debug('using default alue for %s: %s' %
                              (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    @asyncio.coroutine
    def find_all(cls, where=None, args=None, **kw):
        ' find objects by where clause. '
        sql = [cls.__select__]
        if args is None:
            args = []
        if where:
            sql.append('where %s' % (where))
        if kw.get('orderBy') is not None:
            sql.append('order by %s' % (kw['orderBy']))
        limit = kw.get('limit')
        if limit:
            if isinstance(limit, int):
                sql.append('limit ?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('limit ?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = yield from select(' '.join(sql), args)
        return [cls(**r) for r in rs]

    @classmethod
    @asyncio.coroutine
    def find_num(cls, where=None, args=None):
        ' find number by select and where '
        sql = ['select count(*) _num_ from `%s`' % (cls.__table__)]
        if where:
            sql.append('where %s' % (where))
        rs = yield from select(' '.join(sql), args, 1)
        if not rs:
            return 0
        return rs[0].get('_num_', 0)

    @classmethod
    @asyncio.coroutine
    def find(cls, pk):
        'find object by primary key.'
        rs = yield from select('%s where `%s`=?' % (cls.__select__, cls.__pm_key__),
                               [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    @asyncio.coroutine
    def save(self):
        args = list(map(self.get_value_or_def, self.__fields__))
        args.append(self.get_value_or_def(self.__pm_key__))
        rows = yield from execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)

    @asyncio.coroutine
    def update(self):
        args = list(map(self.get, self.__fields__))
        rows = yield from execute(self.__update__, args)
        if rows != 1:
            logging.warn(
                'failed to update by primary key: affected rows: %s' % rows)

    @asyncio.coroutine
    def remove(self):
        args = [self.get(self.__primary_key__)]
        rows = yield from execute(self.__delete__, args)
        if rows != 1:
            logging.warn(
                'failed to remove by primary key: affected rows: %s' % rows)


class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):

    def __init__(self, name=None, primary_key=False, default=None,
                 ddl='varchar(100)'):
        super(StringField, self).__init__(name, ddl, primary_key, default)


class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntergerField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'biginit', primary_key, default)


class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, ' text', False, default)
