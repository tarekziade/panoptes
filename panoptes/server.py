from aiohttp import web

async def dashboard(request):
    return web.Response(text="Panoptes")


app = web.Application()
app.add_routes([web.get('/', dashboard)])
web.run_app(app)

