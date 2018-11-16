from aiohttp import web
#from panoptes.driver import start_session, stop_session
from aiohttp_jinja2 import setup, template
import jinja2
import logging
import os

from panoptes.driver import GeckoClient
from panoptes.database import MetricsDB

here = os.path.dirname(__file__)
app = web.Application()
setup(app, loader=jinja2.FileSystemLoader(os.path.join(here, "templates")))
routes = web.RouteTableDef()
app.gecko = None
app.db = None

async def get_metrics(metrics):
    if app.db is None:
        app.db = MetricsDB()
    # async??
    print(app.db.write_points(metrics))


@routes.get('/')
@template('dashboard.jinja2')
async def dashboard(request):
    return {}

@routes.get('/2')
@template('plots.jinja2')
async def plots(request):
    return {}

@routes.get('/usage')
async def plots(request):
    if app.db is None:
        app.db = MetricsDB()
    return web.json_response(app.db.get_metrics())

@routes.get('/start_session')
async def start_session(request):
    app.gecko = GeckoClient()
    await app.gecko.start(get_metrics)
    return web.json_response({'session_id': app.gecko.session_id})

@routes.post('/visit_url')
async def visit_url(request):
    data = await request.json()
    resp = await app.gecko.visit_url(data['url'])
    return web.json_response(resp)


logging.basicConfig(level=logging.DEBUG)
app.add_routes(routes)
app.router.add_static('/static', os.path.join(here, "static"))
web.run_app(app, reuse_port=True, port=8000)
