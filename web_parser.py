from bs4 import BeautifulSoup
import requests


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
