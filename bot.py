import openpyxl
import telebot
from telebot import types
import os  # Для удаления файла
import sqlite3

API_TOKEN = "6913930971:AAGOoSM3chhSiyy-SBvW2ZrBZ2nUrgqkOq0"
SECRET_KEY = "7324"
bot = telebot.TeleBot(API_TOKEN)
con = sqlite3.connect("datebase.db", check_same_thread=False)
cur = con.cursor()

def parse_excel(file_path):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active  # Работаем с активным листом
    cur.execute("DELETE FROM Users")
    con.commit()
    # Проходим по всем строкам, начиная со второй, предполагая, что первая строка - это заголовки
    for row in sheet.iter_rows(min_row=2, values_only=True):
        uid, name, surname = row[:3]  # Получаем UID, NAME и SURNAME из строки
        status = 0
        sqlite_insert_with_param = """INSERT INTO Users
                              (Name, Surname, CID, Status)
                              VALUES (?, ?, ?, ?);"""

        data_tuple = (name, surname, uid, status)
        cur.execute(sqlite_insert_with_param, data_tuple)
        con.commit()
        print(f"UID: {uid}, NAME: {name}, SURNAME: {surname}")

    # После вывода данных в консоль, удаляем файл
    os.remove(file_path)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    # Проверяем, есть ли пользователь в базе данных
    cur.execute("SELECT * FROM Acount WHERE Id_chat=?", (user_id,))
    existing_user = cur.fetchone()

    if existing_user is None:
        bot.reply_to(message, "Ошибка: вы не зарегистрированы.")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Скачать пример XLSX файла", callback_data="get_excel"))
        bot.reply_to(message, "Добрый день, пришлите пожалуйста xlsx файл.", reply_markup=markup)



@bot.message_handler(commands=['7324'])
def add_user(message):
    try:
        param = message.from_user.first_name, message.from_user.id
        sqlResquest = """INSERT INTO Acount (Name, Id_chat) VALUES (?, ?)"""
        cur.execute(sqlResquest, param)
        con.commit()
        bot.send_message(message.chat.id, "Код успешно введен")
    except:
        bot.send_message(message.chat.id, "Ваш код уже был активирован")



@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "get_excel":
        with open("example_excel.xlsx", "rb") as file:  # Предполагаем, что у вас есть этот файл
            bot.send_document(call.message.chat.id, file)


@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    # Проверяем, есть ли пользователь в базе данных
    cur.execute("SELECT * FROM Acount WHERE Id_chat=?", (user_id,))
    existing_user = cur.fetchone()

    if existing_user is None:
        bot.reply_to(message, "Ошибка: вы не зарегистрированы.")
    else:
        if message.document.mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_path = f"temp_{message.document.file_id}.xlsx"
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            bot.reply_to(message, "Файл успешно загружен. Обрабатываем данные...")

            # Теперь распарсим xlsx файл, выведем информацию из него и удалим файл
            parse_excel(file_path)
            bot.reply_to(message, "Данные успешно загружены!")
        else:
            bot.reply_to(message, "Пожалуйста, отправьте файл в формате .xlsx.")


if __name__ == "__main__":
    bot.polling()
