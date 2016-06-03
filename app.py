import logging
import asyncio
import os
import json
import time
from datetime import datetime
from aiohttp import web

logging.basicConfig(level=logging.INFO)


def index(request):
    return web.Response(body=b'<h1>Awesome</h1>')


# this is a decorator, the 'init' func is arg
@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('Server start at http://127.0.0.1:9000...')
    return srv


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()
