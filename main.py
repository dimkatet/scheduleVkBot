import sqlite3
import psycopg2
import vk_api
import time
import calendar
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_bot import VkBot
from datetime import datetime, date
from threading import Thread


def mailing():
    while(1):
        t1 = time.time()
        conn = psycopg2.connect(dbname='vkBotDataBase', user='postgres', 
                        password='dimka211', host='localhost')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE time='" + time.strftime("%H.%M", time.localtime()) + "'")
        result = cursor.fetchall()
        if result != []:
            bot = VkBot(result[0][0], conn)
            message = ''
            now = datetime.now()
            next_day = calendar.weekday(now.year, now.month, now.day) + 1
            cursor.execute("SELECT * FROM day WHERE id=" + str(result[0][0] * 10 + next_day))
            result = cursor.fetchall()
            print(result)
            if result != []:
                message += "Расписание на завтра: \n"
                for i in result:
                    message += i[1] + '  ' + i[0] + '\n'
                bot.send_message(message=message)
        conn.close()
        t2 = time.time()
        t = t2 - t1
        time.sleep(60 - t)

def waiting():
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
        
            if event.to_me:
                request = event.text            
                bot = VkBot(event.user_id, conn)
                bot.request_handler(request)

        
token = '0432359308d97807e0b3933df66d7180bb1d3bba4462e907100e7d9d5120c47c1ec87bab271570a99559d'

conn = psycopg2.connect(dbname='vkBotDataBase', user='postgres', 
                        password='dimka211', host='localhost')

vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
VkBot.set_BOT(vk_session)
longpoll = VkLongPoll(vk_session)


t1 = Thread(target=waiting)
t2 = Thread(target=mailing)
t1.start()
t2.start()
