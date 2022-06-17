from pathlib import Path
from typing import Optional, List
import os

import aiohttp_jinja2
import aiopg.sa

from aiohttp import web,ClientSession
from aiohttp_tokenauth import token_auth_middleware

from aiochclient import ChClient

import jinja2

from stiflers_mom.routes import init_routes
from stiflers_mom.utils.common import init_config

from dotenv import load_dotenv



#from stiflers_mom.cron import hourly

path = Path(__file__).parent

def load_env():
    load_dotenv()

    if os.getenv("TOKEN") is None:
        logging.log(logging.FATAL,
            "TOKEN is not specified. Please pass TOKEN as env variable")
        exit(1)

def init_jinja2(app: web.Application) -> None:
    '''
    Initialize jinja2 template for application.
    '''
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(str(path / 'templates'))
    )

# clickhouse part

async def init_ch_client(app: web.Application):
    app['http_session'] = ClientSession()
    app['ch'] = ChClient(app['http_session'], **app['config']['clickhouse'])

    # is_alive = await app['ch'].is_alive()
    # print("is_alive",is_alive)


async def close_ch_client(app: web.Application):
    await app['http_session'].close()

# / end of clickhouse part /


async def database(app: web.Application) -> None:
    '''
    A function that, when the server is started, connects to postgresql,
    and after stopping it breaks the connection (after yield)
    '''
    config = app['config']['postgres']
    #config = {"user": "mom", "password": "stifler", "database": "stiflers_mom", "port": "5432", "host": "10.147.99.24" }

    engine = await aiopg.sa.create_engine(**config)
    app['db'] = engine

    #await hourly.next(app)

    yield

    app['db'].close()
    await app['db'].wait_closed()


def init_app(config: Optional[List[str]] = None) -> web.Application:
    #t = app['config']['app']['token']
    load_env()

    async def user_loader(token: str):
        """Checks that token is valid
        """
        user = None

        if token == os.getenv("TOKEN"):
            user = {'uuid': 'user'}            
        return user    

    app = web.Application(middlewares=[token_auth_middleware(user_loader)])

    init_jinja2(app)
    init_config(app, config=config)
    init_routes(app)

    app.on_startup.append(init_ch_client)
    app.on_cleanup.append(close_ch_client)    

    app.cleanup_ctx.extend([
        database,
    ])

    

    return app
