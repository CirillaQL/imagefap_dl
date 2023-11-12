from yarl import URL
import requests
from bs4 import BeautifulSoup
import re
import os
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
    raise RuntimeError(f"Could not detect gallery ID from {url}.")\
    
def get_image_page_urls(url, gallery_id):
    response = requests.get(url=url)
    cached_source_code = BeautifulSoup(response.content, 'html.parser')
    links = []
    elems = cached_source_code.select('a')
    for elem in elems:
        link = elem.get("href")
        if link is None:
            continue
        if link.startswith("/"):
            link = f"https://www.imagefap.com{link}"
        if link not in links:
            links.append(link)
    image_page_urls = []
    for link in links:
        url_struct = urlparse(link)
        regex_pattern = re.compile("\/photo\/(\w+)\/")
        if regex_pattern.match(url_struct.path) is None:
            continue
        query_str = f"gid={gallery_id}"
        if query_str not in url_struct.query:
            continue
        image_page_urls.append(link)
    return image_page_urls

def get_all_image_url(image_list, url, page_offset, gallery_id):
    response = requests.get(url=url)
    soup = BeautifulSoup(response.text, 'html.parser')
    a_href_li_list = soup.select('.thumbs > li > a')
    temp_image_list = []
    for href in a_href_li_list:
        temp_image_list.append(href)
    if len(temp_image_list) < 24:
        image_list.extend(temp_image_list)
        print("get all image original url")
        return
    else:
        # 找到第24个图片的id
        image_list.extend(temp_image_list)
        page_offset = page_offset + 24
        last_image_id = temp_image_list[23]["imageid"]
        new_url =  "https://www.imagefap.com/photo/{id}/?gid={gid}&idx={count}&partial=true".format(id=last_image_id, gid=gallery_id,count=page_offset)
        time.sleep(2)
        print("continue to get image url... ")
        get_all_image_url(image_list=image_list, url=new_url, page_offset=page_offset, gallery_id=gallery_id)

def download_image(image_urls_list, output_dir, gallery_id):
    real_download_dir = output_dir+"/"+gallery_id
    if not os.path.exists(real_download_dir):
        os.makedirs(real_download_dir)
    for url in image_urls_list:
        image_url = url["original"]
        a = URL(image_url)
        image_name = a.parts[-1]
        image_data = requests.get(image_url).content
        with open(real_download_dir+"/"+image_name, 'wb') as f:
            f.write(image_data)
        print(image_name," download success")
        time.sleep(0.5)

def main(url, output_dir):
    print(f"Trying to download images from {url}")
    gallery_id = get_gallery_id(url=url)
    image_page_urls = get_image_page_urls(url, gallery_id)
    first_url = image_page_urls[0]
    count = 0
    ans = []
    get_all_image_url(ans, first_url, count, gallery_id)
    download_image(ans, output_dir, gallery_id)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Downloads images from the ImageFap gallery."
    )
    parser.add_argument(
        "gallery_url",
        type=str,
        help="url of the gallery"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="./download", help="Path to the output folder where images will be saved"
    )
    args = parser.parse_args()
    main(args.gallery_url, args.output)
