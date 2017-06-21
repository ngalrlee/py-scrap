import requests
import re
# import pickle
import configparser
import telepot
import time
import json

import asyncio

import telepot.aio

from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

inifile = '../pyscrap_data/pyscrap.ini'
internal_data = []
TOKEN = []
global_chat_list = []
item_list = []

# 내부 설정 로드
def myinit():
    global internal_data
    global TOKEN
    global global_chat_list
    global item_list

    internal_data = configparser.RawConfigParser()
    internal_data.read(inifile)

    TOKEN = internal_data.get('DEFAULT', 'TOKEN')
    global_chat_list = json.load(internal_data.get('CHATID', 'ID'))
    item_list = json.load(internal_data.get('SCRAP_IKEA', 'ITEMS'))


def inisave():
    with open(inifile, 'wb') as fp:
        internal_data.write(fp)


@asyncio.coroutine
def monitorStat():
    while True:
        for item_id in item_list:
            print(item_id)
            s = requests.session()
            item_desc = []
            item_stock = []
            try:
                item_desc = s.get('http://www.ikea.com/kr/ko/catalog/products/' + item_id + '/')
                item_stock = s.get('http://www.ikea.com/kr/ko/iows/catalog/availability/' + item_id)

            except:
                print("[" + time.asctime() + "] error exception")
            s.close()

            result_desc = BeautifulSoup(item_desc.text, 'html.parser')
            result_stock = ET.fromstring(item_stock.text)

            # 결과 페이지 파싱
            tmp_desc = result_desc.find_all("meta", attrs={"property": "og:title"})[0]['content']
            tmp_stock = result_stock.findall(".//localStore[@buCode='373']//availableStock")[0].text

            tmp_result = "[" + tmp_desc + "] 재고개수 : " + tmp_stock

            print("[" + time.asctime() + "] " + str(tmp_result))
            print("[" + time.asctime() + "] send to : " + ",".join(str(x) for x in global_chat_list))
            for ids in global_chat_list:
                asyncio.ensure_future(bot.sendMessage(ids, tmp_result))

        # 30분 휴식
        yield from asyncio.sleep(1800)


def handle(msg):
    print(msg);
    try:
        chat_id = msg['chat']['id']
        command = msg['text']
    except:
        pass

    if command == "/start":
        global_chat_list.append(chat_id)
        internal_data.set('CHATID', 'ID', json.dump(global_chat_list))
        asyncio.ensure_future(inisave())
        asyncio.ensure_future(bot.sendMessage(chat_id, ",".join(str(x) for x in global_chat_list)))

    if command == "/list":
        _x = ""
        for x in item_list:
            _x = _x + '\n' + (','.join(str(k) for k in x))
        print(_x)

        asyncio.ensure_future(bot.sendMessage(chat_id, _x))

    print(chat_id, command)


TOKEN = []
myinit()
bot = telepot.aio.Bot(TOKEN)
loop = asyncio.get_event_loop()

loop.create_task(bot.message_loop(handle))
asyncio.ensure_future(monitorStat())

print("[" + time.asctime() + "] Listening ...")

loop.run_forever()
