import logging
import asyncio
import os
import json
import time
from datetime import datetime
from aiohttp import web
from orm import create_pool, close_pool
from coroweb import add_routes, add_static
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.INFO)


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


@asyncio.coroutine
def logger_factory(app, handler):
    @asyncio.coroutine
    def logger(request):
        # write log
        logging.info('Request: %s %s' % (request.method, request.path))
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError(
                'handler:%s is not coroutine func' % handler.__name__)
        else:
            return (yield from handler(request))
    return logger


@asyncio.coroutine
def response_factory(app, handler):
    @asyncio.coroutine
    def response(request):
        r = yield from handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.context_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            resp = web.Response(body=r.encode('utf-8'))
            resp.context_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(
                    body=json.dumps(r, ensure_ascii=False,
                                    default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(
                    body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


db_config = {
    'user': 'www-data',
    'password': 'www-data',
    'db': 'awesome'
}


# this is a decorator, the 'init' func is arg
@asyncio.coroutine
def init(loop):
    yield from create_pool(loop=loop, host='localhost', port=3306, user='www-data', password='www-data', db='awesome')
    app = web.Application(loop=loop, middlewares=[
        logger_factory, response_factory])
    # app.on_shutdown.append(on_close)
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
    # app.router.add_route('GET', '/', index)
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
