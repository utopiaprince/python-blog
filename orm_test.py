import orm
import asyncio
from models import User, Blog, Comment

loop = asyncio.get_event_loop()

db_config = {
    'user': 'www-data',
    'password': 'www-data',
    'db': 'awesome'
}


def test(loop):
    yield from orm.create_pool(loop, **db_config)
    u = User(name='Test', email='test@example.com', passwd='123456', image='about:blank')

    yield from u.save()
    yield from u.find()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop))
    loop.close()
    if loop.is_closed():
        sys.exit(0)
