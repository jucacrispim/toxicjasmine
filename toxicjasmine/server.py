# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor
import os
from http.server import (
    SimpleHTTPRequestHandler,
    ThreadingHTTPServer,
    _get_best_family
)


_THREAD_POOL = ThreadPoolExecutor()


class ToxicjasmineServer:

    def __init__(self, port, root_dir='.'):
        self.port = port
        self.root_dir = root_dir
        self._last_cwd = None
        self._httpd = None

    def run(self):
        self._last_cwd = os.getcwd()
        os.chdir(self.root_dir)
        try:
            ThreadingHTTPServer.address_family, addr = _get_best_family(
                None, self.port)
            SimpleHTTPRequestHandler.protocol_version = "HTTP/1.0"
            with ThreadingHTTPServer(addr, SimpleHTTPRequestHandler) as httpd:
                self._httpd = httpd
                host, port = self._httpd.socket.getsockname()[:2]
                url_host = f'[{host}]' if ':' in host else host
                print(
                    f"Serving HTTP on {host} port {self.port} "
                    f"(http://{url_host}:{port}/) ..."
                )

                self._httpd.serve_forever()

        finally:
            os.chdir(self._last_cwd)


    def start(self):
        _THREAD_POOL.submit(self.run)

    def stop(self):
        self._httpd.shutdown()
        os.chdir(self._last_cwd)
        self._httpd = None
        self._last_cwd = None
