from influxdb import InfluxDBClient
import random
import datetime
from collections import defaultdict

def now(hours=None):
    if hours is not None:
        res = datetime.datetime.now() - datetime.timedelta(hours=hours)
    else:
        res = datetime.datetime.now()
    return res.strftime("%Y-%m-%dT%H:%M:%SZ")


# crappy ad-hoc diff queries
class MetricsDB:
    def __init__(self):
        self.client = InfluxDBClient('localhost', 8086, 'root', 'root', 'gecko')
        self.client.create_database('gecko')
        def m_():
            return [0, 0]

        self.diffs = defaultdict(m_)
        self.measures = 0

    def reset_data(self):
        self.client.query("delete from network_io;")
        self.client.query("delete from performance;")
        self.client.query("delete from process;")

    def write_metrics(self, metrics):
        points = []
        timestamp = now()
        self.measures += 1
        proc_data = metrics['value'].get('proc', [])
        for item in proc_data:
            point = {"measurement": "process",
                    "tags": {"filename": item['filename'], 'type': item['type'],
                             "childID": item.get('childID', -1)},
                     "time": timestamp,
                     "fields": {"cpuKernel": item['cpuKernel'],
                                "cpuUser": item['cpuUser'],
                                "residentSetSize": item['residentSetSize'],
                                "virtualMemorySize": item['virtualMemorySize'],
                                "pid": item['pid']
                                }
                    }
            points.append(point)

        io_data = metrics['value'].get('io', [])
        changed = []
        for item in io_data:
            location = item['location']
            if location.endswith('osfile_async_worker.js'):
                continue
            # marionette XXX
            # XXX get the local IP to make this filter portable
            if '192.168.1.' in location:
                continue
            rx = item['rx']
            tx = item['tx']
            old_rx, old_tx = self.diffs[location]
            if self.measures == 1:
                self.diffs[location] = rx, tx
                continue

            rx -= old_rx
            if rx < 0:
                rx = 0
            tx -= old_tx
            if tx < 0:
                tx = 0
            self.diffs[location] = rx, tx
            point = {"measurement": "network_io",
                     "tags": {"location": location},
                     "time": timestamp,
                     "fields": {"rx": rx, "tx": tx}
                    }
            changed.append(location)
            points.append(point)

        for location, __ in self.diffs.items():
            if location in changed:
                continue
            self.diffs[location] = 0, 0

        changed = []
        for item in metrics['value'].get('performance', []):
            count = 0
            for subitem in item['items']:
                if subitem['category'] == 8:
                    continue
                count += subitem['count']
            host = item['host']
            duration = item['duration']
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

            point = {"measurement": "performance",
                     "tags": {"host": host},
                     "time": timestamp,
                     "fields": {"duration_": duration,
                                "dispatches": count}
                    }
            self.diffs[host] = count, duration
            changed.append(host)
            points.append(point)

        for location, __ in self.diffs.items():
            if location in changed:
                continue
            self.diffs[location] = 0, 0

        print("Writing %d points" % len(points))
        return self.client.write_points(points)

    def get_proc_metrics(self):

        timestamp = now(24)
        res = self.client.query("""
    select
        cpuKernel,
        cpuUser,
        residentSetSize,
        virtualMemorySize from process
    where time > '%s'
                    """ % (timestamp))


        if 'series' not in res.raw:
            return []
        def _s():
            return {'kernel': 0, 'user':0, 'residentSetSize':0 ,
                    'virtualMemorySize':0}
        by_time = defaultdict(_s)
        for i in res.raw['series'][0]['values']:
            time = i[0]
            by_time[time]['kernel'] += i[1]
            by_time[time]['user'] += i[2]
            by_time[time]['residentSetSize'] += i[3]
            by_time[time]['virtualMemorySize'] += i[4]
            by_time[time]['time'] = time
        return list(by_time.values())

    def get_perf_metrics(self):
        timestamp = now(24)  # XXX replace by uptime
        res = self.client.query("""
        select dispatches, duration_ from performance
        where time > '%s'
        group by dispatches, duration_
        """ % timestamp)
        # XXX should be in query
        def make():
            return {'duration': 0, 'count': 0}
        items = defaultdict(make)
        if 'series' not in res.raw:
            return []
        for value in res.raw['series'][0]['values']:
            items[value[0]]['count'] += value[1]
            items[value[0]]['duration'] += (value[2] / 1000.)
        res = []
        for key, value in items.items():
            value['time'] = key
            res.append(value)
        return res

    # XXX convert in full influxdb query
    def get_top_io(self):
        p = self.client.query("select location, rx, tx from network_io")
        def p_():
            return {'rx': 0, 'tx': 0}
        hosts = defaultdict(p_)
        for item in p['network_io']:
            hosts[item['location']]['rx'] += item['rx']
            hosts[item['location']]['tx'] += item['tx']
        def _s(host):
            if not host.startswith('file'):
                return host
            return host.split('/')[-1]
        data = [[data['rx'], data['tx'], _s(host)] for host, data in hosts.items()
                if data['rx'] > 0 or
                data['tx'] > 0]

        def _by_read(item):
            return -(item[0]+item[1])

        data.sort(key=_by_read)

        return [{'rx': item[0],
                 'tx': item[1],
                 'location': item[2]}
                 for item in data[:5]]

    def get_io_metrics(self):
        timestamp = now(24)
        res = self.client.query("""
        select rx, tx from network_io
        where time > '%s'
        group by rx, tx
        """ % timestamp)
        if 'series' not in res.raw:
            return []
        # XXX should be in query
        def make():
            return {'rx': 0, 'tx': 0}
        items = defaultdict(make)
        for value in res.raw['series'][0]['values']:
            items[value[0]]['tx'] += value[1]
            items[value[0]]['rx'] += value[2]
        res = []
        for key, value in items.items():
            value['time'] = key
            res.append(value)
        return res

if __name__ == '__main__':
    m = MetricsDB()
    m.write_metrics()
