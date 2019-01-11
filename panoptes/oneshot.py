import sys
import asyncio
import signal
import functools
import pdb
from concurrent.futures import CancelledError

from scipy import stats
from async_generator import asynccontextmanager
import matplotlib.pyplot as plt

from panoptes.driver import GeckoClient
from panoptes.database import MetricsDB

loop = asyncio.get_event_loop()


def log(msg):
    print(msg)


_MACH = "/Users/tarek/Dev/gecko/mozilla-central-opt/mach"
_GECKO = None


@asynccontextmanager
async def geckodriver():
    global _GECKO
    log("Starting geckodriver")
    _GECKO = await asyncio.create_subprocess_exec(*[_MACH, "geckodriver"])
    try:
        await asyncio.sleep(5)
        yield _GECKO
    finally:
        await _kill_gecko(False)


async def _kill_gecko(cancel=True):
    global _GECKO
    if _GECKO is None:
        return
    log("Terminating geckodriver")
    try:
        _GECKO.terminate()
    except ProcessLookupError:
        pass
    else:
        await _GECKO.wait()
        try:
            _GECKO.kill()
        except ProcessLookupError:
            pass
    _GECKO = None
    if not cancel:
        return
    for task in asyncio.Task.all_tasks():
        task.cancel()


def bye(geckoclient, database):
    loop.create_task(geckoclient.close())
    loop.create_task(_kill_gecko())


async def write_metrics(db, data):
    log("Writing metrics...")
    db.write_metrics(data)


def check_data(db):
    perf = db.get_perf_metrics()
    # now applying linear regression on metrics
    y = [m['dom'] for m in db.get_firefox_memory_metrics()]
    x = range(len(y))
    print(str(y))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    log('DOM Memory Correlation coefficient %.2f' % r_value)
    plt.plot(x, y, 'o', label='DOM Size')
    plt.plot(x, intercept + slope*x, 'r', label='fitted line')
    plt.legend()
    plt.show()

async def run_scenario(url, collect_time=3600):
    gecko = GeckoClient()
    db = MetricsDB()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, callback=functools.partial(bye, gecko, db))

    async with geckodriver():
        await gecko.start(functools.partial(write_metrics, db))
        log("Emptying any existing data")
        db.reset_data()
        await asyncio.sleep(5)
        log("Visiting %s" % url)
        resp = await gecko.visit_url(url)
        # TODO make the script re-startable.
        log("Collect data for %s seconds" % collect_time)
        await asyncio.sleep(collect_time)

    await gecko.close()

    check_data(db)
    # TODO generate a report


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://ziade.org"

    if len(sys.argv) > 2:
        collect_time = int(sys.argv[2])
    else:
        collect_time = 3600
    try:
        loop.run_until_complete(run_scenario(url, collect_time))
    except CancelledError:
        pass
    finally:
        if not loop.is_closed():
            loop.close()
