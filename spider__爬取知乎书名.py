import json
import re
import requests
from multiprocessing import Pool
from requests.exceptions import RequestException

def pare_one_page(html):

    #pattern = re.compile('<dd>.*?board-index.*?">(\d+)</i>.*?data-src="(.*?)".*?</a>.*?class="name".*?title="(.*?)".*?</a>.*?class="start">(.*?)</p>.*?releasetime">(.*?)</p>.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>')
    pattern = re.compile('<dd.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?</a>.*?name.*?title="(.*?)".*?star">(.*?)</p>.*?releasetime">'+
                         '(.*?)</p>.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?',re.S)
    items = re.findall(pattern,html)
    for item in items:
        yield {
            "index":item[0],
            "src":item[1],
            "name":item[2],
            "star":item[3].strip()[3:],
            "releasetime":item[4].strip()[5:],
            "score":item[5] + item[6]
        }
def write_file(content):
    with open("result.txt",'a',encoding='utf-8') as f:
        f.write(json.dumps(content,ensure_ascii=False)+'\n')
        f.close()

def get_url(url):
    try:
        html = requests.get(url)
        if html.status_code == 200:
            return html.text
    except RequestException:
        return None


def main(offset):
    url = "http://maoyan.com/board/4?offset=" + str(offset)
    html = get_url(url)
    content = pare_one_page(html)
    for content1 in content:
        write_file(content1)
        print(content1)

if __name__ == "__main__":
    pool = Pool()
    pool.map(main,[i*10 for i in range(10)])
