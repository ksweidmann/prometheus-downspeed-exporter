#!/usr/bin/env python3
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess as sp
import shlex
from urllib.parse import parse_qs
from urllib.parse import urlparse
import logging
import json
import os

def check(host, timeout, size):
    cmd = 'curl --connect-timeout {t} -w "@{p}curl.txt" -sLo /dev/null http://{h}/{s}MB.bin'.format(t=timeout,
                                                                                                    h=host,
                                                                                                    s=size,
                                                                                                    p=PATH)
    output = list()
    logger.info(cmd)
    cmd_output = sp.Popen(shlex.split(cmd), stdout=sp.PIPE, stderr=sp.PIPE).communicate()

    try:
        jsout = json.loads(cmd_output[0])
        jsout['status'] = 0
    except:
        jsout = dict()
        jsout['status'] = 1
    logger.info('Result: {}'.format(jsout))
    if jsout['status'] == 0:
        if int(jsout['code']) == 200:
            speed_bytes = int(float(jsout['speed']))
        else:
            speed_bytes = 0
    else:
        speed_bytes = 0

    output.append('speed{{host="{host}", metric="avg_bits"}} {v}'.format(host=host, v=speed_bytes * 8))
    output.append('speed{{host="{host}", metric="avg_bytes"}} {v}'.format(host=host, v=speed_bytes))
    output.append('')
    return output


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path).query
        value = parse_qs(parsed_path)
        address = value['target'][0]

        if "size" in value:
            size = value['size'][0]
        else:
            size = 1

        if "timeout" in value:
            timeout = value['timeout'][0]
        else:
            timeout = 5

        result = check(host=address, size=size, timeout=timeout)
        message = '\n'.join(result).encode('utf8')

        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)
        return


if __name__ == '__main__':
    PATH=os.environ['DOWNSPEED_PATH']
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    port = 8085
    logger.info('Starting server port {}, use <Ctrl-C> to stop'.format(port))
    server = ThreadedHTTPServer(('0.0.0.0', port), GetHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('Server stopped')
