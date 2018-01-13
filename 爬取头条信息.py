import json
from _md5 import md5
import os
from multiprocessing.pool import Pool
import pymongo
import re
import requests
from urllib.parse import urlencode
from config import *
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from json.decoder import JSONDecodeError

client = pymongo.MongoClient(MONGO_URL,connect=False)
db = client[MONGO_DB]

def get_one_page(offset,keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': 20,
        'cur_tab': 1,
        'from':'search_tab'
    }

    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print("请求索引也出错")
        return None

def parse_page_index(html):
    try:
        data = json.loads(html)
        if data and "data" in data.keys():
            for item in data.get("data"):
                yield item.get("article_url")
    except JSONDecodeError:
        pass

def get_page_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print("请求详情页有误也出错")
        return None

def parse_page_detail(html,url):
    soup = BeautifulSoup(html,'lxml')
    result = soup.select('title')
    title = soup.select('title')[0].get_text() if result else ''
    image_pattern = re.compile('gallery: JSON.parse\("(.*?)"\),',re.S)
    result = re.search(image_pattern,html)

    if result:
        data = json.loads(result.group(1).replace('\\',''))
        if data and 'sub_images' in data.keys():
            print(data.get('sub_images'))
            sub_images = data.get('sub_images')
            images = [item.get('url') for item in sub_images]
            for image in images:download_image(image)
            return{
                'title':title,
                'url':url,
                'images':images
            }


def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('存储到Mongo成功')
        return True
    return False

def download_image(url):
    print('正在下载',url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except RequestException:
        print("请求图片出错")
        return None

def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(),md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):
        with open(file_path,'wb') as f:
            f.write(content)
            f.close()


def main(offset):
    html = get_one_page(0,KEYWORD)
    for url in parse_page_index(html):
        html = get_page_detail(url)
        if html:
            result = parse_page_detail(html,url)
            if result:save_to_mongo(result)

if __name__ == "__main__":
    # main(0)
    pool = Pool()
    groups =([x * 20 for x in range(GROUP_START,GROUP_END+1)])
    print(groups)
    pool.map(main,groups)
    pool.close()
    pool.join()
