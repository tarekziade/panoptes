from influxdb import InfluxDBClient
import random
import datetime

class MetricsDB:
    def __init__(self):
        self.client = InfluxDBClient('localhost', 8086, 'root', 'root', 'gecko')
        self.client.create_database('gecko')

    def write_metrics(self, metrics):
        # TODO convert Firefox metrics into InfluxDB data
        points = [{
        "measurement": "cpu_load_short",
        "tags": {
            "host": "server01",
            "region": "us-west"
        },
        "time": datetime.datetime.now().isoformat(),
        "fields": {
            "value": random.randint(1, 100)
        }
        }
        ]
        return self.client.write_points(points)

    def get_metrics(self):
        res = self.client.query('select value from cpu_load_short;')
        return res.raw['series']

if __name__ == '__main__':
    m = MetricsDB()
    m.write_metrics()
