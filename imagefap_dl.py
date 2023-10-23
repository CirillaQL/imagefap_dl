from yarl import URL
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time 

def get_gallery_id(url):
    url_struct = urlparse(url)

    if not (url_struct.hostname == "www.imagefap.com" or url_struct.hostname == "imagefap.com"):
        raise RuntimeError(f"Expected a gallery from imagefap.com, instead given link to {url}.")

    path = url_struct.path.split("/")
    path.pop(0)
    queries = url_struct.query.split("&")

    match path[0]:
        case "gallery" | "pictures":
            return path[1]
        case "photo" | "gallery.php":
            for query in queries:
                if query[:4] == "gid=":
                    return query[4:]
    raise RuntimeError(f"Could not detect gallery ID from {url}.")