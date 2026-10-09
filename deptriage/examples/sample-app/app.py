"""Small sample app: it imports requests and yaml, but not flask."""

import requests
import yaml


def load_config(path):
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ping(url):
    return requests.get(url, timeout=5).status_code
