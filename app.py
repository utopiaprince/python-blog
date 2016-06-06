import logging
import asyncio
import os
import json
import time
from datetime import datetime
from aiohttp import web
from orm import create_pool, close_pool

logging.basicConfig(level=logging.INFO)


def index(request):
    return web.Response(body=b'<h1>Awesome</h1>')


@asyncio.coroutine
def on_close(app):
    yield from close_pool()


# this is a decorator, the 'init' func is arg
@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    # app.on_shutdown.append(on_close)
    app.router.add_route('GET', '/', index)
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
