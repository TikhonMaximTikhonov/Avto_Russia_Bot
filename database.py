import sqlalchemy.ext.declarative as dec
import sqlalchemy.orm as orm
import sqlalchemy

from sqlalchemy.orm import Session
from json import loads, dumps

SqlAlchemyBase = dec.declarative_base()


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

    def create_user(self, user_id):
        session = self.create_session()
        if session.query(User).filter(User.user_id == user_id).first() is None:
            user = User(user_id)
            session.add(user)
        session.commit()

    def save_user_data(self, user_id, mode=None, additional_list=None, errors_list=None, ticket_number=None,
                       answer_number=None, true_answer=None, false_answers=None, hint=None):
        session = self.create_session()
        user = session.query(User).filter(User.user_id == user_id).first()
        if mode:
            user.mode = mode
        if additional_list:
            user.additional_list = additional_list
        if errors_list:
            user.errors_list = dumps(errors_list)
        if ticket_number:
            user.ticket_number = ticket_number
        if answer_number:
            user.answer_number = answer_number
        if true_answer:
            user.true_answer = true_answer
        if false_answers:
            user.false_answers = dumps(false_answers)
        if hint:
            user.hint = hint
        session.commit()

    def return_false_answers(self, user_id):
        user = self.create_session().query(User).filter(User.user_id == user_id).first()
        if user.false_answers is not None:
            return loads(user.false_answers)
        return []

    def return_true_answer(self, user_id):
        user = self.create_session().query(User).filter(User.user_id == user_id).first()
        return user.true_answer

    def return_mode(self, user_id):
        user = self.create_session().query(User).filter(User.user_id == user_id).first()
        return user.mode

    def return_ticket_data(self, user_id):
        session = self.create_session()
        user = session.query(User).filter(User.user_id == user_id).first()
        return [user.ticket_number, user.answer_number + 1]

    def return_ticket_number(self, user_id):
        session = self.create_session()
        user = session.query(User).filter(User.user_id == user_id).first()
        return user.ticket_number

    def return_answer_number(self, user_id):
        session = self.create_session()
        user = session.query(User).filter(User.user_id == user_id).first()
        return user.answer_number

    def return_hint(self, user_id):
        session = self.create_session()
        user = session.query(User).filter(User.user_id == user_id).first()
        return user.hint

    def return_errors_list(self, user_id):
        session = self.create_session()
        user = session.query(User).filter(User.user_id == user_id).first()
        return loads(user.errors_list)

    def reset_to_zero_errors_list(self, user_id, key):
        session = self.create_session()
        user = session.query(User).filter(User.user_id == user_id).first()
        directory = loads(user.errors_list)
        directory[str(key)] = []
        user.errors_list = dumps(directory)
        session.commit()

    def save_in_errors_list(self, user_id, key, error):
        session = self.create_session()
        user = session.query(User).filter(User.user_id == user_id).first()
        directory = loads(user.errors_list)
        directory[str(key)].append(error)
        user.errors_list = dumps(directory)
        session.commit()


class User(SqlAlchemyBase):
    __tablename__ = "users"
    user_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, unique=True, nullable=False)
    mode = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    additional_list = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    errors_list = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    ticket_number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    answer_number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    true_answer = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    false_answers = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    hint = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    def __init__(self, user_id):
        self.user_id = int(user_id)
        self.errors_list = dumps({})
