# -*- coding: utf-8 -*-

import telebot
# telebot.logger.setLevel(__import__('logging').DEBUG)

from bs4 import BeautifulSoup
import requests

import sqlalchemy
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

bot = telebot.TeleBot(open("token.txt", "r", encoding="utf8").read().strip())

SqlAlchemyBase = dec.declarative_base()


class User(SqlAlchemyBase):
    __tablename__ = "users"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, unique=True, nullable=False)
    ticket_number = sqlalchemy.Column(sqlalchemy.Float, nullable=True)
    correct_answer = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    hint = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    def __init__(self, user_id, ticket_number=0, correct_answer=None, hint=None):
        self.id = int(user_id)
        self.ticket_number = float(ticket_number)
        self.correct_answer = correct_answer
        self.hint = hint


class Parser:
    def __init__(self, ticket_number, task_number):
        url = f"https://avto-russia.ru/pdd_abma1b1/bilet{ticket_number}.html"
        self.parser = BeautifulSoup(requests.get(url).text, "lxml")
        self.task_number = int(task_number) - 1
        self.all_sorted_data = {}

    def return_data(self):
        self.write_ticket_numbers()
        self.write_picture_url()
        self.write_question()
        self.write_answer_options()
        self.write_hint()
        self.write_correct_answer()
        return self.all_sorted_data

    def write_ticket_numbers(self):
        ticket_number = self.parser.body.findAll("div", {
            "style": "margin: 0 auto !important; float: none !important; display: block; width:auto; max-width:725px;"
        })[self.task_number]
        self.all_sorted_data["ticket_number"] = ticket_number.text

    def write_picture_url(self):
        ticket_number = self.all_sorted_data["ticket_number"].replace("Билет ", "").split(" - Вопрос ")
        url_add = f"pdd-{ticket_number[0].rjust(2, '0')}-{ticket_number[1].rjust(2, '0')}.jpg"
        if requests.get("https://avto-russia.ru/pdd_abma1b1/images/" + url_add).status_code == 200:
            self.all_sorted_data["picture_url"] = "https://avto-russia.ru/pdd_abma1b1/images/" + url_add
        else:
            self.all_sorted_data["picture_url"] = "https://avto-russia.ru/pdd_abma1b1/images/blank.jpg"

    def write_question(self):
        questions = self.parser.body.findAll("div", {"style": "padding:5px; font-weight: bold;"})[self.task_number]
        self.all_sorted_data["question"] = questions.text

    def write_answer_options(self):
        answers_options = self.parser.body.findAll("div", {"style": "padding:5px;"})
        index = -1
        for answer_options in answers_options:
            if answer_options.text.startswith("1. "):
                index += 1
                if index == self.task_number:
                    self.all_sorted_data["answer_options"] = [answer_options.text.split(". ")[1].strip()]
                    continue
            if index == self.task_number:
                self.all_sorted_data["answer_options"].append(answer_options.text.split(". ")[1].strip())

    def write_hint(self):
        hint = self.parser.body.findAll("div", {"class": "well"})[self.task_number]
        if "Вопрос:" in hint.text:
            self.all_sorted_data["hint"] = hint.text.split("Вопрос:")[0].strip()
        else:
            self.all_sorted_data["hint"] = hint.text

    def write_correct_answer(self):
        correct_answer = self.parser.body.findAll("span", {"style": "color:#008000"})[self.task_number]
        self.all_sorted_data["correct_answer"] = correct_answer.text


class DataBase:
    def __init__(self, db_file):
        self.factory = None
        self.main_init(db_file)

    def main_init(self, db_file):
        if self.factory:
            return
        conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
        engine = sqlalchemy.create_engine(conn_str, echo=False)
        self.factory = orm.sessionmaker(bind=engine)
        SqlAlchemyBase.metadata.create_all(engine)

    def create_session(self) -> Session:
        return self.factory()

    def save_user_data(self, user_id, user_data):
        session = self.create_session()
        if session.query(User).filter(User.id == user_id).first() is None:
            user = User(user_id, *user_data)
            session.add(user)
        else:
            user = session.query(User).filter(User.id == user_id).first()
            user.ticket_number, user.correct_answer, user.hint = user_data
        session.commit()

    def return_ticket_number(self, user_id):
        session = self.create_session()
        user = session.query(User).filter(User.id == user_id).first()
        return user.ticket_number


def create_markup(main_buttons_data):
    markup = telebot.types.ReplyKeyboardMarkup(True)
    for button_data in main_buttons_data:
        if type(button_data) == list:
            buttons = []
            for button_name in button_data:
                buttons.append(telebot.types.KeyboardButton(button_name))
            markup.row(*buttons)
        else:
            markup.row(telebot.types.KeyboardButton(button_data))
    return markup


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.from_user.id, "Выберите один из предложенных режимов",
                     reply_markup=create_markup(["Выбрать билет", "Работа над ошибками", "Тотальный тест"]))


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Выбрать билет")
def choosing_ticket(message):
    bot.send_message(message.from_user.id, "Выберите билет", reply_markup=create_markup([
        [*range(1, 9)], [*range(9, 17)], [*range(17, 25)], [*range(25, 33)], [*range(33, 41)], "🎲 Случайный билет 🎲"
    ]))


@bot.message_handler(content_types=["text"])
def text(message):
    if message.text.isdigit() and 0 < int(message.text) < 21 or message.text == "Следующий вопрос":
        if message.text.isdigit() and 0 < int(message.text) < 21:
            full_task_number = [int(message.text), 1]
            task = Parser(*full_task_number).return_data()
            db.save_user_data(message.from_user.id,
                              [round(float(message.text) + 0.02, 2), task["correct_answer"], task["hint"]])
        else:
            full_task_number = list(map(int, str(db.return_ticket_number(message.from_user.id)).split(".")))
            task = Parser(*full_task_number).return_data()
            db.save_user_data(message.from_user.id, [
                round(db.return_ticket_number(message.from_user.id) + 0.01, 2), task["correct_answer"], task["hint"]])
        bot.send_message(message.from_user.id, task["ticket_number"])
        bot.send_photo(message.from_user.id, task["picture_url"], task["question"])

    # bot.send_message(message.from_user.id, "\n".join(task["answer_options"]))


db = DataBase("database.db")
print("База данных открыта/создана")

bot.polling()
