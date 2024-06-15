# -*- coding: utf-8 -*-

import os
import http.client
from toxicjasmine import server


TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', 'testdata')


def test_run():
    srv = server.ToxicjasmineServer(8000, TEST_DATA_DIR)
    srv.start()
    response = _get('bla.js')
    assert response.status == 200
    srv.stop()


def _get(path):
    host = "localhost:8000"
    c = 0
    while c < 10:
        print(c)
        try:
            conn = http.client.HTTPConnection(host)
            conn.request("GET", path, headers={"Host": host})
        except Exception:
            c += 1
        else:
            break
    response = conn.getresponse()
    return response
