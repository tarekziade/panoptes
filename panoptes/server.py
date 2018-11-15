from aiohttp import web
#from panoptes.driver import start_session, stop_session
from aiohttp_jinja2 import setup, template
import jinja2
import logging
import os

here = os.path.dirname(__file__)
app = web.Application()
setup(app, loader=jinja2.FileSystemLoader(os.path.join(here, "templates")))
routes = web.RouteTableDef()

@routes.get('/')
@template('dashboard.jinja2')
async def dashboard(request):
    return {}


logging.basicConfig(level=logging.DEBUG)
app.add_routes(routes)

app.router.add_static('/static', os.path.join(here, "static"))
web.run_app(app, reuse_port=True, port=8000)

