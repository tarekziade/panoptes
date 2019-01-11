import sys
import asyncio
import signal
import functools

from panoptes.driver import GeckoClient
from panoptes.database import MetricsDB

loop = asyncio.get_event_loop()

def log(msg):
    print(msg)


def bye():
    loop.stop()

async def write_metrics(db, data):
    log(data)
    db.write_metrics(data)

async def run_scenario(url):
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, callback=bye)
    log("Starting geckodriver")
    gecko = GeckoClient()
    db = MetricsDB()
    await gecko.start(functools.partial(write_metrics, db))
    log("Emptying any existing data")
    db.reset_data()
    await asyncio.sleep(5)
    log("Visiting %s" % url)
    resp = await gecko.visit_url(url)
    # TODO make the script re-startable.
    log("Collect data for one hour")
    await asyncio.sleep(3600)
    # TODO analyze the data
    # TODO generate a report


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = 'https://ziade.org'
    try:
        loop.run_until_complete(run_scenario(url))
    finally:
        if not loop.is_closed():
            loop.close()
