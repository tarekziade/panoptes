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

    def write_metrics(self, metrics):
        self.measures += 1
        io_data = metrics['value'].get('io', [])
        points = []
        timestamp = now()
        for item in io_data:
            location = item['location']
            rx = item['rx']
            tx = item['tx']
            old_rx, old_tx = self.diffs[location]
            if self.measures == 1:
                self.diffs[location] = rx, tx
                continue

            rx -= old_rx
            tx -= old_tx
            self.diffs[location] = rx, tx
            point = {"measurement": "network_io",
                     "tags": {"location": location},
                     "time": timestamp,
                     "fields": {"rx": rx, "tx": tx}
                    }
            points.append(point)

        for item in metrics['value'].get('performance', []):
            count = 0
            for subitem in item['items']:
               count += subitem['count']

            point = {"measurement": "performance",
                     "tags": {"host": item['host']},
                     "time": timestamp,
                     "fields": {"duration": item['duration'],
                                "count": count}
                    }
            points.append(point)

        print("Writing %d points" % len(points))
        return self.client.write_points(points)

    def get_metrics(self):
        timestamp = now(24)
        res = self.client.query("""
        select rx, tx from network_io
        where time > '%s'
        group by rx, tx
        """ % timestamp)
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
