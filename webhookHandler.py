# -*- coding: utf-8 -*-

from urllib.parse import urljoin
from urllib.parse import urlencode
import urllib.request as urlrequest
import json
from config import WEBHOOK_URL


def notify(**kwargs):
    """
    Send message to slack API
    """
    return send(kwargs)

def send(payload):
    """
    Send payload to slack API
    """
    url = WEBHOOK_URL
    opener = urlrequest.build_opener(urlrequest.HTTPHandler())
    payload_json = json.dumps(payload)
    data = urlencode({"payload": payload_json})
    req = urlrequest.Request(url)
    response = opener.open(req, data.encode('utf-8')).read()
    return response.decode('utf-8')