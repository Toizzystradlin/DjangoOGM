import mysql.connector


def send_message_1(query_id, name, inv, place, cause, msg):  # функция для отправки уведомления о новой заявке мастеру
    import telebot
    from telebot import apihelper
    #apihelper.proxy = {'https': '192.168.0.100:50278'}  #
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        passwd='12345',
        port='3306',
        database='ogm2'
    )
    cursor3 = db.cursor(buffered=True)
    sql = "SELECT tg_id FROM employees WHERE (master = '1')"
    cursor3.execute(sql)
    masters_id = cursor3.fetchall()
    print(masters_id)

    bot_2 = telebot.TeleBot('1044824865:AAGACPaLwqHdOMn5HZamAmSljkoDvSwOiBw')

    keyboard = telebot.types.InlineKeyboardMarkup()
    key_choose = telebot.types.InlineKeyboardButton('Назначить ...', callback_data='choose')
    keyboard.add(key_choose)
    key_postpone = telebot.types.InlineKeyboardButton('Отложить', callback_data='postpone')
    keyboard.add(key_postpone)

    #392674056
    for i in masters_id:
        try:
            bot_2.send_message(i[0], "*НОВАЯ ЗАЯВКА*" + "\n" + "*id_заявки: *" + str(
            query_id) + "\n" + "*Наименование: *" + name + "\n" +
                       "*Инв.№: *" + inv + "\n" + "*Участок: *" + place + "\n" + "*Причина поломки: *" +
                       cause + "\n" + "*Сообщение: *" + msg, reply_markup=keyboard, parse_mode="Markdown")
        except:
            pass


def send_message_4(id_employee, query_id):  # функция для отправки уведомления сотруднику
    import telebot
    from telebot import apihelper
    #apihelper.proxy = {'https': '192.168.0.100:50278'}  #
    bot_3 = telebot.TeleBot('1048673690:AAHPT1BfgqOoQ1bBXT1dcSiClLzwwOq0sPU')
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        passwd='12345',
        port='3306',
        database='ogm2'
    )
    cursor3 = db.cursor(buffered=True)
    sql = "SELECT equipment.eq_name, equipment.invnum, equipment.eq_type, equipment.area, " \
          "queries.reason, queries.msg FROM " \
          "equipment JOIN queries ON ((queries.query_id = %s) AND (queries.eq_id = equipment.eq_id)) "
    val = (query_id,)
    cursor3.execute(sql, val)
    msg = cursor3.fetchone()
    print(msg)

    keyboard = telebot.types.InlineKeyboardMarkup()
    key_start_now = telebot.types.InlineKeyboardButton('Начинаю выполнение', callback_data='start_now')
    keyboard.add(key_start_now)
    #key_start_later = telebot.types.InlineKeyboardButton('Отложить', callback_data='start_later')
    #keyboard.add(key_start_later)

    bot_3.send_message(id_employee, "У вас новая заявка" + "\n" + "*id_заявки: *" + str(query_id) + "\n" +
                       "*Оборудование: *" + msg[0] + "\n" + "*Инв.№: *" + msg[1] + "\n" +
                       "*Тип станка: *" + msg[2] + "\n" + "*Участок: *" + msg[3] + "\n" +
                       "*Причина поломки: *" + msg[4] + "\n" + "*Сообщение: *" + str(msg[5]), reply_markup=keyboard,
                       parse_mode="Markdown")
    cursor3.close()

def send_message_work(id_employee, work_id):
    import telebot
    from telebot import apihelper
    # apihelper.proxy = {'https': '192.168.0.100:50278'}  #
    bot_3 = telebot.TeleBot('1048673690:AAHPT1BfgqOoQ1bBXT1dcSiClLzwwOq0sPU')
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        passwd='12345',
        port='3306',
        database='ogm2'
    )
    cursor3 = db.cursor()
    sql = "SELECT what FROM unstated_works WHERE work_id = %s"
    val = (work_id,)
    cursor3.execute(sql, val)
    msg = cursor3.fetchone()
    print(msg)

    keyboard = telebot.types.InlineKeyboardMarkup()
    key_start_now = telebot.types.InlineKeyboardButton('Начинаю выполнение', callback_data='start_now_work')
    keyboard.add(key_start_now)
    # key_start_later = telebot.types.InlineKeyboardButton('Отложить', callback_data='start_later')
    # keyboard.add(key_start_later)

    bot_3.send_message(id_employee, "У вас новая нештатная работа" + "\n" + "*id_работы: *" + str(work_id) + "\n" +
                        "*Сообщение: *" + str(msg[0]), reply_markup=keyboard,
                       parse_mode="Markdown")
    cursor3.close()

def send_message_to(id_employee, to_id):  # функция для отправки уведомления сотруднику
    import telebot
    from telebot import apihelper
    #apihelper.proxy = {'https': '192.168.0.100:50278'}  #
    bot_3 = telebot.TeleBot('1048673690:AAHPT1BfgqOoQ1bBXT1dcSiClLzwwOq0sPU')
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        passwd='12345',
        port='3306',
        database='ogm2'
    )
    cursor3 = db.cursor(buffered=True)
    sql = "SELECT equipment.eq_name, equipment.invnum, equipment.eq_type, equipment.area, maintenance.start_time " \
          "FROM " \
          "equipment JOIN maintenance ON ((maintenance.id = %s) AND (maintenance.eq_id = equipment.eq_id)) "
    val = (to_id,)
    cursor3.execute(sql, val)
    msg = cursor3.fetchone()

    keyboard = telebot.types.InlineKeyboardMarkup()
    key_start_now = telebot.types.InlineKeyboardButton('Начать ТО', callback_data='go_to')
    keyboard.add(key_start_now)

    bot_3.send_message(id_employee, "*Новое ТО.*" + "\n" + "*id_TO: *" + str(to_id) + "\n" +
                       "*Оборудование: *" + msg[0] + "\n" + "*Инв.№: *" + msg[1] + "\n" +
                       "*Тип станка: *" + msg[2] + "\n" + "*Участок: *" + msg[3] + "\n" "*Дата: *" + str(msg[4])[:10], reply_markup=keyboard,
                       parse_mode="Markdown")
    cursor3.close()