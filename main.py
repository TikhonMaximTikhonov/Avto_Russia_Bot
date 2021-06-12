from database import DataBase
from web_parser import Parser

import telebot

from copy import copy

# telebot.logger.setLevel(__import__('logging').DEBUG)
bot = telebot.TeleBot(open("token.txt", "r", encoding="utf8").read().strip())


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


def send_questions(message, full_task_number):
    task = Parser(*full_task_number).return_data()
    bot.send_message(message.from_user.id, task["ticket_number"])
    if task["picture_url"] != "https://avto-russia.ru/pdd_abma1b1/images/blank.jpg":
        bot.send_photo(message.from_user.id, task["picture_url"], task["question"],
                       reply_markup=create_markup(task["answer_options"]))
    else:
        bot.send_message(message.from_user.id, task["question"],
                         reply_markup=create_markup(task["answer_options"]))

    false_answers = copy(task["answer_options"])
    false_answers.remove(task["correct_answer"])
    return task, false_answers


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Главное меню")
@bot.message_handler(commands=["start"])
def start_function(message):
    data_base.create_user(message.from_user.id)
    bot.send_message(message.from_user.id, "Выберите один из предложенных режимов",
                     reply_markup=create_markup(["Выбрать билет"]))


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Выбрать билет")
def selected_ticket_function(message):
    data_base.save_user_data(message.from_user.id, mode="selected_ticket")
    bot.send_message(message.from_user.id, "Выберите билет", reply_markup=create_markup([
        [*range(1, 9)], [*range(9, 17)], [*range(17, 25)], [*range(25, 33)], [*range(33, 41)],
        ["🎲 Случайный билет 🎲", "Главное меню"]
    ]))


@bot.message_handler(content_types=["text"],
                     func=lambda message: message.text in data_base.return_false_answers(message.from_user.id))
def false_answers_function(message):
    ticket_number = data_base.return_ticket_number(message.from_user.id)
    answer_number = data_base.return_answer_number(message.from_user.id)
    data_base.save_in_errors_list(message.from_user.id, ticket_number, answer_number)

    bot.send_message(message.from_user.id, "НЕ Верно", reply_markup=create_markup(["Следующий вопрос"]))
    bot.send_message(message.from_user.id, data_base.return_hint(message.from_user.id))


@bot.message_handler(content_types=["text"],
                     func=lambda message: (message.text == data_base.return_true_answer(message.from_user.id) and
                                           data_base.return_answer_number(message.from_user.id) < 20))
def true_answer_function(message):
    bot.send_message(message.from_user.id, "Верно", reply_markup=create_markup(["Следующий вопрос"]))


@bot.message_handler(content_types=["text"],
                     func=lambda message: (message.text == data_base.return_true_answer(message.from_user.id) and
                                           data_base.return_answer_number(message.from_user.id) == 20))
def last_true_answer_function(message):
    bot.send_message(message.from_user.id, "Верно", reply_markup=create_markup(["Главное меню"]))


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Следующий вопрос")
def next_question_function(message):
    task, false_answers = send_questions(message, data_base.return_ticket_data(message.from_user.id))
    data_base.save_user_data(message.from_user.id, answer_number=int(task["ticket_number"].split(" - Вопрос ")[1]),
                             true_answer=task["correct_answer"], false_answers=false_answers, hint=task["hint"])


@bot.message_handler(content_types=["text"],
                     func=lambda message: (message.text.isdigit() and 0 < int(message.text) < 41 and
                                           data_base.return_mode(message.from_user.id) == "selected_ticket"))
def first_question_function(message):
    data_base.reset_to_zero_errors_list(message.from_user.id, message.text)
    task, false_answers = send_questions(message, [int(message.text), 1])
    data_base.save_user_data(message.from_user.id, ticket_number=int(message.text), answer_number=1,
                             true_answer=task["correct_answer"], false_answers=false_answers, hint=task["hint"])


data_base = DataBase("database.db")
print("База данных открыта/создана")

bot.polling()
