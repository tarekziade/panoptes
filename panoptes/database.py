from influxdb import InfluxDBClient
from datetime import datetime
from collections import defaultdict
import socket


def InfluxItems(*fields):
    def init_fields(*fields):
        def _init():
            map = {}
            for field in fields:
                map[field] = 0
            return map

        return _init

    return defaultdict(init_fields(*fields))


# crappy ad-hoc diff queries
class MetricsDB:
    def __init__(self):
        self.localhost = socket.gethostbyname(socket.gethostname())
        self.client = InfluxDBClient("localhost", 8086, "root", "root", "gecko")
        self.client.create_database("gecko")
        self.diffs = defaultdict(lambda: [0, 0])
        self.pids_diffs = defaultdict(lambda: [0, 0])
        self.io_diffs = defaultdict(lambda: [0, 0])
        self.measures = 0
        self.session_start = None

    def reset_data(self):
        self.client.drop_database("gecko")
        self.client.create_database("gecko")
        self.session_start = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def write_metrics(self, metrics):
        points = []
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.measures += 1
        refresh_rate = 60
        proc_data = metrics["value"].get("proc", [])
        for item in proc_data:
            kernel = item["cpuKernel"]
            user = item["cpuUser"]
            pid = item["pid"]
            old_kernel, old_user = self.pids_diffs[pid]
            if self.measures == 1:
                self.pids_diffs[pid] = kernel, user
                continue

            self.pids_diffs[pid] = kernel, user
            kernel_p = float((kernel - old_kernel) / (refresh_rate * 10000000.0))
            user_p = float((user - old_user) / (refresh_rate * 10000000.0))
            point = {
                "measurement": "process",
                "tags": {
                    "filename": item["filename"],
                    "type": item["type"],
                    "childID": item.get("childID", -1),
                },
                "time": timestamp,
                "fields": {
                    "cpuKernel": kernel_p,
                    "cpuUser": user_p,
                    "residentSetSize": int(item["residentSetSize"] / 1024.0 / 1024.0),
                    "virtualMemorySize": int(
                        item["virtualMemorySize"] / 1024.0 / 1024.0
                    ),
                    "pid": pid,
                },
            }
            points.append(point)

        io_data = metrics["value"].get("io", [])
        changed = []
        for item in io_data:
            location = item["location"]
            if location.endswith("osfile_async_worker.js"):
                continue
            if self.localhost in location:
                continue
            if 'socket' in location:
                print(location)
            rx = item["rx"]
            tx = item["tx"]
            old_rx, old_tx = self.io_diffs[location]
            if self.measures == 1:
                self.io_diffs[location] = rx, tx
                continue

            rx -= old_rx
            if rx < 0:
                rx = 0
            tx -= old_tx
            if tx < 0:
                tx = 0

            self.io_diffs[location] = old_rx + rx, old_tx + tx
            point = {
                "measurement": "network_io",
                "tags": {"location": location},
                "time": timestamp,
                "fields": {"rx": rx, "tx": tx},
            }
            print("location %s, %d %d" % (location, rx, tx))
            points.append(point)
            changed.append(location)

        changed = []
        for item in metrics["value"].get("performance", []):
            count = 0
            for subitem in item["items"]:
                if subitem["category"] == 8:
                    continue
                count += subitem["count"]
            host = item["host"]
            duration = item["duration"]
            if self.measures == 1:
                self.diffs[host] = count, duration
                continue
            old_count, old_duration = self.diffs[host]
            count -= old_count
            duration -= old_duration
            if count < 0:
                count = 0
            if duration < 0:
                duration = 0

            self.diffs[host] = count + old_count, duration + old_duration
            point = {
                "measurement": "performance",
                "tags": {"host": host},
                "time": timestamp,
                "fields": {"duration_": duration, "dispatches": count},
            }
            points.append(point)
            changed.append(host)

            heap = item["memoryInfo"].get("GCHeapUsage", 0)
            domDom = item["memoryInfo"].get("domDom", 0)
            domOther = item["memoryInfo"].get("domOther", 0)
            domStyle = item["memoryInfo"].get("domStyle", 0)
            dom = domDom + domOther + domStyle
            audio = item["memoryInfo"]["media"].get("audioSize", 0)
            video = item["memoryInfo"]["media"].get("videoSize", 0)
            res = item["memoryInfo"]["media"].get("resourcesSize", 0)

            point = {
                "measurement": "firefox_memory",
                "tags": {"host": host},
                "time": timestamp,
                "fields": {
                    "heap": heap,
                    "dom": dom,
                    "audio": audio,
                    "video": video,
                    "resources": res,
                },
            }
            points.append(point)

        print("Writing %d points" % len(points))
        return self.client.write_points(points)

    def get_proc_metrics(self):

        if self.session_start is None:
            return []

        res = self.client.query(
            """
    select
        cpuKernel,
        cpuUser,
        residentSetSize,
        virtualMemorySize from process
    where time >= '%s'
                    """
            % (self.session_start)
        )

        if "series" not in res.raw:
            return []
        by_time = InfluxItems("kernel", "user", "residentSetSize", "virtualMemorySize")
        for i in res.raw["series"][0]["values"]:
            time = i[0]
            by_time[time]["kernel"] += i[1]
            by_time[time]["user"] += i[2]
            by_time[time]["residentSetSize"] += i[3]
            by_time[time]["virtualMemorySize"] += i[4]
            by_time[time]["time"] = time
        return list(by_time.values())

    def get_perf_metrics(self):
        if self.session_start is None:
            return []

        res = self.client.query(
            """
        select dispatches, duration_ from performance
        where time >= '%s'
        group by dispatches, duration_
        """
            % self.session_start
        )
        items = InfluxItems("duration", "count")
        if "series" not in res.raw:
            return []
        for value in res.raw["series"][0]["values"]:
            items[value[0]]["count"] += value[1]
            items[value[0]]["duration"] += value[2] / 1000.0
        res = []
        for key, value in items.items():
            value["time"] = key
            res.append(value)
        return res

    def get_firefox_memory_metrics(self):

        if self.session_start is None:
            return []

        res = self.client.query(
            """
        select heap, dom, audio, video, resources from firefox_memory
        where time >= '%s'
        group by heap, dom, audio, video, resources
        """
            % self.session_start
        )

        items = InfluxItems("heap", "dom", "audio", "video", "resources")
        if "series" not in res.raw:
            return []
        for value in res.raw["series"][0]["values"]:
            items[value[0]]["heap"] += value[1]
            items[value[0]]["dom"] += value[2]
            items[value[0]]["audio"] += value[3]
            items[value[0]]["video"] += value[4]
            items[value[0]]["resources"] += value[5]
        res = []
        for key, value in items.items():
            value["time"] = key
            res.append(value)
        return res

    # XXX convert in full influxdb query
    def get_top_io(self):

        if self.session_start is None:
            return []

        p = self.client.query("select location, rx, tx from network_io")
        hosts = InfluxItems("rx", "tx")
        for item in p["network_io"]:
            hosts[item["location"]]["rx"] += item["rx"]
            hosts[item["location"]]["tx"] += item["tx"]

        def _s(host):
            if not host.startswith("file"):
                return host
            return host.split("/")[-1]

        data = [
            [data["rx"], data["tx"], _s(host)]
            for host, data in hosts.items()
            if data["rx"] > 0 or data["tx"] > 0
        ]

        def _by_read(item):
            return -(item[0] + item[1])

        data.sort(key=_by_read)

        return [
            {"rx": item[0], "tx": item[1], "location": item[2]} for item in data[:5]
        ]

    def get_io_metrics(self):

        if self.session_start is None:
            return []

        res = self.client.query(
            """
        select rx, tx from network_io
        where time >= '%s'
        group by rx, tx
        """
            % self.session_start
        )
        if "series" not in res.raw:
            return []
        items = InfluxItems("rx", "tx")
        for value in res.raw["series"][0]["values"]:
            items[value[0]]["tx"] += value[1]
            items[value[0]]["rx"] += value[2]
        res = []
        for key, value in items.items():
            value["time"] = key
            res.append(value)
        return res


if __name__ == "__main__":
    m = MetricsDB()
    m.write_metrics()
