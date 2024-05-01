from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException
import time
import requests
import sqlite3

con = sqlite3.connect("datebase.db")
cur = con.cursor()
token = "6913930971:AAGOoSM3chhSiyy-SBvW2ZrBZ2nUrgqkOq0"


def get_card_uid(reader):
    """Functions"""
    try:
        connection = reader.createConnection()
        connection.connect()
        get_uid_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        data, sw1, sw2 = connection.transmit(get_uid_command)
        if sw1 == 0x90 and sw2 == 0x00:
            uid = toHexString(data)
            user_info = cur.execute("SELECT Name, Surname, Status FROM Users WHERE CID=?", (uid,)).fetchone()
            if user_info is not None:
                Name, Surname, Status = user_info
                # Преобразование статуса из строки в целое число, если требуется
                Status = int(Status)
                text_status = "уход" if Status == 1 else "приход"
                new_status = 0 if Status == 1 else 1  # Обновление статуса на противоположный

                users = cur.execute("SELECT id_chat FROM Acount").fetchall()
                for user in users:
                    us = user[0]
                    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={us}&text={Name} {Surname} {text_status}"
                    print(requests.get(url).json())  # Эта строка отсылает сообщение

                # Обновляем статус в базе данных на противоположный
                cur.execute("UPDATE Users SET Status=? WHERE CID=?", (new_status, uid))
                con.commit()
            else:
                users = cur.execute("SELECT id_chat FROM Acount").fetchall()
                for user in users:
                    us = user[0]
                    text = "Неизвестная карта"
                    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={us}&text={text} + {uid}"
                    print(requests.get(url).json())  # Эта строка отсылает сообщение
    except NoCardException:
        print("Карта не обнаружена, поднесите карту.")
    except Exception as e:
        print(f"Ошибка при чтении карты: {e}")


def monitor_card_presence():
    while True:
        r = readers()
        if not r:
            print("Считыватель не обнаружен. Ожидание подключения...")
            time.sleep(1)  # Делаем паузу перед следующей проверкой
            continue

        print("Используемый считыватель:", r[0])
        print("Ожидание карты...")

        try:
            get_card_uid(r[0])
        except NoCardException:
            print("Карта не обнаружена, поднесите карту.")
        except Exception as e:
            print(f"Ошибка при чтении карты: {e}")

        time.sleep(0.3)  # Использование асинхронной задержки для предотвращения постоянного опроса

if __name__ == "__main__":
    monitor_card_presence()
