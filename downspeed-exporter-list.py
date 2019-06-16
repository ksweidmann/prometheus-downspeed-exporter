#!/usr/bin/env python3
import subprocess as sp
import time
import yaml
import json
import shlex
import os
from prometheus_client import Gauge
from prometheus_client import start_http_server


def curl(h, timeout, size):
    output = {
        'avg_bytes': 0,
        'avg_bits': 0
    }
    cmd = 'curl --connect-timeout {t} -w "@{p}curl.txt" -sLo /dev/null http://{h}/{s}MB.bin'.format(t=timeout,
                                                                                                     h=h,
                                                                                                     s=size,
                                                                                                     p=PATH)
    cmd_output = sp.Popen(shlex.split(cmd), stdout=sp.PIPE, stderr=sp.PIPE).communicate()

    try:
        jsout = json.loads(cmd_output[0])
        jsout['status'] = 0
    except:
        jsout = dict()
        jsout['status'] = 1

    if jsout['status'] == 0:
        if int(jsout['code']) == 200:
            speed_bytes = int(float(jsout['speed']))
        else:
            speed_bytes = 0
    else:
        speed_bytes = 0

    output['avg_bytes'] = speed_bytes
    output['avg_bits'] = speed_bytes * 8
    return output


def check(hosts):
    r = dict()

    for h in hosts:
        r[h] = curl(h=h, timeout=1, size=10)
    return r


def get_config(file):
    try:
        with open(file, 'r') as stream:
            try:
                c = yaml.load(stream, Loader=yaml.SafeLoader)
                return c
            except yaml.YAMLError as exc:
                print(exc)
                return False
    except:
        return False


if __name__ == '__main__':
    PATH = os.environ['DOWNSPEED_PATH']
    config = get_config(file=PATH + "hosts.yml")
    metrics = Gauge('speed', 'speed measurment', ['host', 'metric'])
    start_http_server(port=1222, addr='0.0.0.0')
    while True:
        result = check(hosts=config['targets'])
        for host in result:
            for metric, value in result[host].items():
                metrics.labels(host, metric).set(value)
        time.sleep(900)
