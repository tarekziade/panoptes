import datetime
import os
import aiohttp
import asyncio


def now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


JS_SCRIPT = os.path.join(os.path.dirname(__file__), "metricsCollector.js")
with open(JS_SCRIPT) as f:
    metrics_script = f.read()

_CAP = {
    "capabilities": {
        "alwaysMatch": {
            "acceptInsecureCerts": True,
            "moz:firefoxOptions": {
                # "binary":
                # "/Users/tarek/Dev/gecko/mozilla-central-talos/objdir-osx/dist/Nightly.app/Contents/MacOS/firefox",
                # "args": [
                #    "-no-remote", "-foreground",
                #    "-profile", "profile-default"],
                "prefs": {"io.activity.enabled": True}
            },
        }
    }
}


class GeckoClient:
    def __init__(self, host="http://localhost:4444", metrics_interval=60):
        self.actions = []
        self.host = host
        self.session_url = host + "/session"
        self.session = aiohttp.ClientSession()
        self.session_id = None
        self.capabilities = None
        self.metrics_cb = None
        self.metrics_interval = metrics_interval
        self.started_at = None

    def started(self):
        return self.started_at is not None

    def get_uptime(self):
        if self.started_at is None:
            return
        uptime = datetime.datetime.now() - self.started_at
        return {"value": uptime.total_seconds()}

    async def call_metrics(self):
        while self.session_id is not None:
            await self.metrics_cb(await self.get_metrics())
            await asyncio.sleep(self.metrics_interval)

    def session_call(self, method, path, json=None):
        meth = getattr(self.session, method.lower())
        return meth(self.session_url + path, json=json)

    async def start(self, metrics_cb=None):
        self.actions.append(("start", now()))
        async with self.session.post(self.host + "/session", json=_CAP) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise Exception(resp.status)
        self.session_id = data["value"]["sessionId"]
        self.capabilities = data["value"]["capabilities"]
        self.session_url = self.host + "/session/" + self.session_id
        self.metrics_cb = metrics_cb
        if metrics_cb is not None:
            loop = asyncio.get_event_loop()
            loop.create_task(self.call_metrics())
        self.started_at = datetime.datetime.now()
        return self.session_id

    async def stop(self):
        self.actions.append(("stop", now()))
        async with self.session.delete(self.session_url) as resp:
            assert resp.status == 200
        self.session_id = None
        self.capabilities = None

    def get_timeline(self):
        return [{"time": time, "action": action} for action, time in self.actions]

    async def visit_url(self, url):
        self.actions.append(("visit_url", now()))
        data = {"context": "content"}
        async with self.session_call("POST", "/moz/context", json=data) as resp:
            assert resp.status == 200
        data = {"url": url}
        async with self.session_call("POST", "/url", json=data) as resp:
            res = await resp.json()
            print(res)
            assert resp.status == 200
        return res

    async def get_metrics(self):
        data = {"context": "chrome"}
        async with self.session_call("POST", "/moz/context", json=data) as resp:
            assert resp.status == 200
        data = {"script": metrics_script, "args": []}
        async with self.session_call("POST", "/execute/sync", json=data) as resp:
            assert resp.status == 200
            return await resp.json()
