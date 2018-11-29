from aiohttp import web
import asyncio
import base64
import random

# from panoptes.driver import start_session, stop_session
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


def db():
    if app.db is None:
        app.db = MetricsDB()
    return app.db


async def get_metrics(metrics):
    # async??
    print(db().write_metrics(metrics))


@routes.get("/")
@template("dashboard.jinja2")
async def dashboard(request):
    return {}


@routes.get("/tools")
@template("tools.jinja2")
async def tools(request):
    return {'cache': random.randint(1, 999)}


@routes.get("/io_usage")
async def plots(request):
    return web.json_response(db().get_io_metrics())


@routes.get("/proc_usage")
async def most_used(request):
    return web.json_response(db().get_proc_metrics())


@routes.get("/firefox_mem_usage")
async def f_mem(request):
    return web.json_response(db().get_firefox_memory_metrics())


@routes.get("/top_io")
async def top_io(request):
    return web.json_response(db().get_top_io())


@routes.get("/timeline")
async def timeline(request):
    if app.gecko is None:
        return web.json_response([])
    return web.json_response(app.gecko.get_timeline())


@routes.get("/about_support")
async def timeline(request):
    if app.gecko is None:
        return web.json_response([])
    return web.json_response(await app.gecko.get_support())


@routes.get("/perf_usage")
async def plots2(request):
    return web.json_response(db().get_perf_metrics())


@routes.get("/uptime")
async def plots2(request):
    if app.gecko is None:
        return 0
    return web.json_response(app.gecko.get_uptime())


@routes.get("/start_session")
async def start_session(request):
    app.gecko = GeckoClient()
    await app.gecko.start(get_metrics)
    db().reset_data()
    return web.json_response({"session_id": app.gecko.session_id})


@routes.post("/visit_url")
async def visit_url(request):
    if app.gecko is None or not app.gecko.started:
        if app.gecko is None:
            app.gecko = GeckoClient()
        await app.gecko.start(get_metrics)
        db().reset_data()
        await asyncio.sleep(5)
    data = await request.post()
    resp = await app.gecko.visit_url(data["url"])
    return web.HTTPFound(location="/tools")


@routes.get("/take_screenshot")
async def screenshot(request):
    if app.gecko is not None:
        resp = await app.gecko.screenshot()
        img = base64.b64decode(resp['value'])
        with open(os.path.join(here, 'static', 'screenshot.png'), 'wb') as f:
            f.write(img)
    return web.HTTPFound(location="/tools")


logging.basicConfig(level=logging.DEBUG)
app.add_routes(routes)
app.router.add_static("/static", os.path.join(here, "static"))
web.run_app(app, reuse_port=True, port=8000)
