import aiohttp
import asyncio


script = """\
"use strict";

async function getMetrics() {
    let result = await ChromeUtils.requestPerformanceMetrics();
    // XXX add process info
    return result;
}

return getMetrics();
"""

def forward_metrics(data):
    print("Metrics received")

# do a screenshot too => /session/{sessionId}/moz/screenshot/full
# XXX save the session ID and loop on execute/sync calls until we're told to
# stop
async def run():
    url = 'http://localhost:4444/session'
    data = {"capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}}}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            data = await resp.json()
            session_id = data["value"]["sessionId"]
            capabilities = data["value"]["capabilities"]

        print("Starting session %s" % session_id)

        data = {'url': 'http://google.com'}
        async with session.post(url + '/%s/url' % session_id, json=data) as resp:
            assert resp.status == 200
            data = await resp.json()

        """
        async with session.get(url + '/%s/moz/screenshot/full' % session_id) as resp:
            assert resp.status == 200
            data = await resp.json()
        """
        data = {'context': 'chrome'}
        async with session.post(url + '/%s/moz/context' % session_id, json=data) as resp:
            assert resp.status == 200
            data = await resp.json()

        args = []
        data = {"script": script, "args": args}

        for i in range(10):
            async with session.post(url + '/%s/execute/sync' % session_id, json=data) as resp:
                assert resp.status == 200
                forward_metrics(await resp.json())
            await asyncio.sleep(10)

        print("Closing session %s" % session_id)

        async with session.delete(url + '/%s' % session_id) as resp:
            assert resp.status == 200

        print("Bye")

#
#loop = asyncio.get_event_loop()
#loop.run_until_complete(run())
#loop.close()
