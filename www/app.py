import logging
logging.basicConfig(level=logging.INFO)


import asyncio
import os
import json
import time
from datetime import datetime
from aiohttp import web
from orm import create_pool, close_pool
from coroweb import add_routes, add_static
from jinja2 import Environment, FileSystemLoader
from factorys import logger_factory, auth_factory, data_factory, response_factory, datetime_filter


from config.config import configs


def index(request):
    return web.Response(body=b'<h1>Awesome</h1>')


@asyncio.coroutine
def on_close(app):
    yield from close_pool()


def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    for k, v in kw.items():
        if isinstance(v, dict):
            for m, n in v.items():
                print('    argument %s:%s' % (m, n))
        else:
            print('Optional argument %s (*kw):%s' % (k, v))
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
        app['__templating__'] = env


# this is a decorator, the 'init' func is arg
@asyncio.coroutine
def init(loop):
    # yield from create_pool(loop=loop, host='localhost', port=3306, user='www-data', password='www-data', db='awesome')
    yield from create_pool(loop=loop, **configs.db)
    app = web.Application(loop=loop, middlewares=[logger_factory, auth_factory, data_factory, response_factory])
    app.on_shutdown.append(on_close)
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
    handler = app.make_handler()
    srv = yield from loop.create_server(handler, '127.0.0.1', 9000)
    logging.info('Server start at http://127.0.0.1:9000...')
    rs = dict()
    rs['app'] = app
    rs['srv'] = srv
    rs['handler'] = handler
    return rs


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    rs = loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        rs['srv'].close()
        loop.run_until_complete(rs['srv'].wait_closed())
        loop.run_until_complete(rs['app'].shutdown())
        loop.run_until_complete(rs['handler'].finish_connections(60.0))
        loop.run_until_complete(rs['app'].cleanup())
    loop.close()
