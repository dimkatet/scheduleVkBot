import vk_api
import sqlite3
import time
import calendar
import psycopg2
from vk_api import keyboard
from vk_api.utils import get_random_id
from datetime import datetime

class VkBot:

    def __init__(self, user_id, connection):
            print("Bot Object was created.")
            self.COMMAND = ['команды',"Создать", "Прислать", "Оповещение", "Закрыть"]
            self.DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
            self.USER_ID = user_id
            self.CONNECTION = psycopg2.connect(dbname='vkBotDataBase', user='postgres', 
                        password='dimka211', host='localhost')
            self.STAGE = 0
            self.TIME = ''
            self._DAY =  ''
            self._NUM = ''
            self._NAME = ''
            self.load_data()
            

    @classmethod
    def set_BOT(cls, bot):
        cls.BOT = bot

    def load_data(self):
        cursor = self.CONNECTION.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id=" + str(self.USER_ID))
        result = cursor.fetchall()
        if result == []:
            self.init_user()
        else:
            self.TIME = result[0][1]
            self.STAGE = int(result[0][2])
            self._DAY = result[0][3]
            self._NAME = result[0][4]
            self._NUM = result[0][5]

    def init_user(self):
        cursor = self.CONNECTION.cursor()
        cursor.execute("INSERT INTO students VALUES (" + str(self.USER_ID) + ", 0, 0, 0, 0, 0)")
        cursor.execute("INSERT INTO schedule VALUES (" + str(self.USER_ID) + ", 0, 0, 0, 0, 0, 0)")
        


    def update_data(self):
        cursor = self.CONNECTION.cursor()
        cursor.execute("UPDATE students SET stage = '" + str(self.STAGE) + "' WHERE student_id = '" + str(self.USER_ID) + "'")
        cursor.execute("UPDATE students SET day = '" + self._DAY + "' WHERE student_id = '" + str(self.USER_ID) + "'")
        cursor.execute("UPDATE students SET name = '" + self._NAME + "' WHERE student_id = '" + str(self.USER_ID) + "'")
        cursor.execute("UPDATE students SET num = '" + self._NUM + "' WHERE student_id = '" + str(self.USER_ID) + "'")
        self.CONNECTION.commit()

    def clear_meta(self):
        cursor = self.CONNECTION.cursor()
        cursor.execute("UPDATE students SET day = '0' WHERE student_id = '" + str(self.USER_ID) + "'")
        cursor.execute("UPDATE students SET name = '0' WHERE student_id = '" + str(self.USER_ID) + "'")
        cursor.execute("UPDATE students SET num = '0' WHERE student_id = '" + str(self.USER_ID) + "'")

    def clear_schedule(self):
        cursor = self.CONNECTION.cursor()
        for day in self.DAYS:
            cursor.execute("UPDATE schedule SET " + day + "= '0' WHERE group_id = '" + str(self.USER_ID) + "'")
            cursor.execute("DELETE FROM day WHERE id= '" + str(self.USER_ID * 10 + self.DAYS.index(day)) + "'")

    def add_class(self):
        sec = (int(self._NUM) - 1) * 110 * 60 + 28800
        if int(self._NUM) > 3:
            sec += 900
        t = time.strftime("%H.%M", time.gmtime(sec))
        id = self.USER_ID * 10 + self.DAYS.index(self._DAY)
        lesson = (self._NAME, t, '0', id)
        cursor = self.CONNECTION.cursor()
        cursor.execute("SELECT * FROM day WHERE id=" + str(lesson[3]))
        result = cursor.fetchall()
        for rec in result:
            if rec[1] == lesson[1]:
                cursor.execute("DELETE FROM day WHERE id=" + str(lesson[3]) + " AND time='" + lesson[1] + "'")
                break
        cursor.execute("INSERT INTO day VALUES('" + str(lesson[0]) + "', '" + str(lesson[1]) + "', '" + str(lesson[2]) + "', '" + str(lesson[3]) + "')")
        self.CONNECTION.commit

    def add_day(self):
        id = self.USER_ID * 10 + self.DAYS.index(self._DAY)
        cursor = self.CONNECTION.cursor()
        cursor.execute("SELECT * FROM day WHERE id=" + str(id))
        result = cursor.fetchall()
        if result != []:
            cursor.execute("UPDATE schedule SET " + self._DAY + " = '" + str(id) + "' WHERE group_id = '" + str(self.USER_ID) + "'")
        else:
            self.send_message(message = 'Ошибка, попробуйте заново:')
        self.CONNECTION.commit

    def request_handler(self, request):
        if request == self.COMMAND[0]:
            self.STAGE = 0
            self.update_data()
            self.send_command_keyboard()
        elif request == self.COMMAND[1]:
            self.send_creare_keyboard()           
            self.STAGE = 1
            self.update_data()
        elif request == self.COMMAND[2]:
            self.STAGE = 4
            self.update_data()
            self.send_schedule()
        elif request == self.COMMAND[3]:
            self.STAGE = 5
            self.send_mailing_keyboard()
            self.update_data()
        elif request == self.COMMAND[4]:
            self.STAGE = 0
            self.update_data()
            self.clear_meta()
        elif self.STAGE == 1:
            if self.isDay(request):
                self._DAY = request
                self.STAGE = 2
                self.update_data()
                self.send_class_keyboard(request)
            elif request == "Очистить расписание":
                self.clear_schedule()
                self.send_creare_keyboard()           
                self.STAGE = 1
                self.update_data()
            elif request == 'Завершить':
                self.STAGE = 0
                self.update_data()
                self.clear_meta()
        elif self.STAGE == 2:
            if request.isdigit():
                self._NUM = request
                self.STAGE = 3
                self.update_data()
                self.send_message(message = "Напиши название предмета")
            elif request == 'Завершить':
                self.STAGE = 1
                self.update_data()
                self.add_day()
                self.send_creare_keyboard()
        elif self.STAGE == 3:
            if request == 'Завершить':
                self.STAGE = 1
                self.update_data()
                self.add_day()
                self.send_creare_keyboard()
            else:
                self._NAME = request
                self.STAGE = 2
                self.update_data()
                self.send_message(message = "Добавил в расписание")
                self.send_class_keyboard(request)
                self.add_class()
        elif self.STAGE == 4:
            if request == 'Полное':
                self.send_all_schedule()
                self.STAGE = 0
                self.update_data()
            elif request == 'На завтра':
                self.STAGE = 0
                self.send_next_day_schedule()
                self.update_data()
        elif self.STAGE == 5:
            if request == 'Изменить':
                self.STAGE = 6
                self.update_data()
                self.send_message(message="Укажите время оповещения в формате HH.MM")
            elif request == 'Отменить':
                self.cancel_mailing()
                self.send_message(message="Рассылка отменена")
                self.STAGE = 0
                self.update_data()
        elif self.STAGE == 6:
            if self.isTime(request):
                self.set_time(request)
                self.send_message('Время оповещения уставнолено')
                self.STAGE = 0
                self.update_data()
            else:
                self.send_message(message="Не правельный формат времени")
        else:
            self.send_message(message = 'Не понял тебя')
        self.update_data()
        self.CONNECTION.close()

    def send_command_keyboard(self):
        self.KEYBOARD = keyboard.VkKeyboard(one_time = True, inline = False)
        self.KEYBOARD.add_button(label = self.COMMAND[1], color = 'primary')
        self.KEYBOARD.add_line()
        self.KEYBOARD.add_button(label = self.COMMAND[2], color = 'primary')
        self.KEYBOARD.add_line()
        self.KEYBOARD.add_button(label = self.COMMAND[3], color = 'primary')
        self.KEYBOARD.add_line()
        self.KEYBOARD.add_button(label = "Закрыть", color = 'secondary')
        self.send_message(message = 'Выбери', keyboard = self.KEYBOARD.get_keyboard())

    def send_creare_keyboard(self):
        self.KEYBOARD = keyboard.VkKeyboard(one_time = True, inline = False)
        self.KEYBOARD.add_button(label = "Понедельник", color = 'primary')
        self.KEYBOARD.add_button(label = "Вторник", color = 'primary')
        self.KEYBOARD.add_button(label = "Среда", color = 'primary')
        self.KEYBOARD.add_line()
        self.KEYBOARD.add_button(label = "Четверг", color = 'primary')
        self.KEYBOARD.add_button(label = "Пятница", color = 'primary')
        self.KEYBOARD.add_button(label = "Суббота", color = 'primary')
        self.KEYBOARD.add_line()
        self.KEYBOARD.add_button(label = "Очистить расписание", color = 'secondary')
        self.KEYBOARD.add_button(label = "Завершить", color = 'secondary')
        self.send_message(message = 'Выбери день недели.', keyboard=self.KEYBOARD.get_keyboard())

    def send_class_keyboard(self, day):
        self.KEYBOARD = keyboard.VkKeyboard(one_time = True, inline = False)
        self.KEYBOARD.add_button(label = "1", color = 'primary')
        self.KEYBOARD.add_button(label = "2", color = 'primary')
        self.KEYBOARD.add_button(label = "3", color = 'primary')
        self.KEYBOARD.add_line()
        self.KEYBOARD.add_button(label = "4", color = 'primary')
        self.KEYBOARD.add_button(label = "5", color = 'primary')
        self.KEYBOARD.add_button(label = "6", color = 'primary')
        self.KEYBOARD.add_line()
        self.KEYBOARD.add_button(label = "Завершить", color = 'secondary')
        self.send_message("Выберите номер пары", self.KEYBOARD.get_keyboard())

    def send_schedule(self):
        self.KEYBOARD = keyboard.VkKeyboard(one_time = True, inline = False)
        self.KEYBOARD.add_button(label = "Полное", color = 'primary')
        self.KEYBOARD.add_button(label = "На завтра", color = 'primary')
        self.send_message("Какое расписание прислать?", self.KEYBOARD.get_keyboard())

    def send_mailing_keyboard(self):
        self.KEYBOARD = keyboard.VkKeyboard(one_time = True, inline = False)
        self.KEYBOARD.add_button(label = "Изменить", color = 'primary')
        self.KEYBOARD.add_button(label = "Отменить", color = 'secondary')
        self.send_message(message='выбери', keyboard=self.KEYBOARD.get_keyboard())

    def send_all_schedule(self):
        message = ''
        cursor = self.CONNECTION.cursor()
        for i in range(6):
            cursor.execute("SELECT * FROM day WHERE id=" + str(self.USER_ID * 10 + i) + " ORDER BY time")
            result = cursor.fetchall()
            if result != []:
                message += self.DAYS[i] + ':\n'
                for i in result:
                    message += i[1] + '  ' + i[0] + '\n'
                if message != '':
                    self.send_message(message = message)
                message = ''

    def send_next_day_schedule(self):
        message = ''
        now = datetime.now()
        next_day = calendar.weekday(now.year, now.month, now.day)
        if now.hour > 8:
            next_day += 1
        cursor = self.CONNECTION.cursor()
        cursor.execute("SELECT * FROM day WHERE id=" + str(self.USER_ID * 10 + next_day))
        result = cursor.fetchall()
        if result != []:
            message += "Расписание на завтра: \n"
            for i in result:
                message += i[1] + '  ' + i[0] + '\n'
            self.send_message(message = message)
        else:
            self.send_message("Завтра нет пар =)")


    def set_time(self, request):
        cursor = self.CONNECTION.cursor()
        cursor.execute("UPDATE students SET time = '" + request + "' WHERE student_id = '" + str(self.USER_ID) + "'")
        
    def send_message(self, message, keyboard = 0):
        if keyboard != 0:
            self.__class__.BOT.method("messages.send", {'user_id': self.USER_ID, 'random_id': get_random_id(), 'message': message, "keyboard":keyboard})
        else:
            self.__class__.BOT.method("messages.send", {'user_id': self.USER_ID, 'random_id': get_random_id(), 'message': message})

    def send_mailing_time(self):
        cursor = self.CONNECTION.cursor()
        cursor.execute("SELECT time FROM students WHERE student_id=" + str(self.USER_ID))
        result = cursor.fetchall()
        self.send_message(message=result[0][0])

    def cancel_mailing(self):
        cursor = self.CONNECTION.cursor()
        cursor.execute("UPDATE students SET time = '0' WHERE student_id = '" + str(self.USER_ID) + "'")

    def isDay(self, request):
        for day in self.DAYS:
            if day == request:
                return True
        return False

    def isTime(self, request):
        h = request[:2]
        d = request[2]
        m = request[3:5]
        if int(h) >= 0 and int(h) < 24 and int(m) >= 0 and int(m) < 60 and d == '.':
            return True
        else:
            return False