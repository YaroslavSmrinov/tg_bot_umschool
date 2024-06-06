import telebot
from sqlalchemy.orm import sessionmaker
from db import Student, Score, engine
import os
from dotenv import load_dotenv

load_dotenv()
Session = sessionmaker(bind=engine)
TG_TOKEN = os.getenv('TG_TOKEN')
bot = telebot.TeleBot(TG_TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message):
    session = Session()
    existing_student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
    if not existing_student:
        # если юзер подключает тг аккаунт в первый раз - регистрируем его в бд.
        new_student = Student(telegram_id=message.from_user.id)
        session.add(new_student)
        session.commit()
    session.close()
    bot.send_message(message.chat.id, "Привет! Для начала работы зарегистрируйся или войди в свой аккаунт. Введите /register.")


@bot.message_handler(commands=['register'])
def handle_register(message):
    session = Session()
    existing_student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
    if not existing_student.first_name:
        bot.send_message(message.chat.id, "Для регистрации введи своё имя.")
        session.close()
        bot.register_next_step_handler(message, process_first_name_step)
    elif not existing_student.last_name:
        bot.send_message(message.chat.id, "Введи свою фамилию.")
        session.close()
        bot.register_next_step_handler(message, process_last_name_step, existing_student.first_name)


def process_first_name_step(message):
    if message.text.startswith('/'):
        handle_command(message)
        return
    chat_id = message.chat.id
    first_name = message.text
    session = Session()
    existing_student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
    existing_student.first_name = first_name
    session.add(existing_student)
    session.commit()
    session.close()
    bot.send_message(chat_id, "Введи свою фамилию.")
    bot.register_next_step_handler(message, process_last_name_step, first_name)


def process_last_name_step(message, first_name):
    if message.text.startswith('/'):
        handle_command(message)
        return
    chat_id = message.chat.id
    last_name = message.text
    session = Session()
    existing_student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
    existing_student.last_name = last_name
    session.add(existing_student)
    session.commit()
    session.close()
    bot.send_message(chat_id, f"Спасибо, {first_name} {last_name}, ты успешно зарегистрирован!")
    bot.send_message(chat_id, "Настало время ввести баллы. \n /enter_scores")


def handle_command(message):
    chat_id = message.chat.id
    command = message.text.strip().lower()
    if command == '/start':
        handle_start(message)
    elif command == '/register':
        handle_register(message)
    else:
        bot.send_message(chat_id, "Я не знаю такую команду. \n Список команд можно посмотреть тут: /help")


@bot.message_handler(commands=['enter_scores'])
def handle_enter_scores(message):
    bot.send_message(message.chat.id, "Введите свои баллы ЕГЭ в формате: \n Предмет балл")
    bot.register_next_step_handler(message, process_scores_step)


def process_scores_step(message):
    chat_id = message.chat.id
    if message.text.startswith('/'):
        handle_command(message)
        return
    scores_data = message.text.split()
    if not len(scores_data) > 1:
        bot.send_message(chat_id, "Не подходящий формат. Похоже, ты забыл пробел.")
        return
    subject, score = message.text.rsplit(' ', 1)
    try:
        score = int(score)
    except ValueError:
        bot.send_message(chat_id, "Не подходящий формат. Баллы должны быть введены числом от 0 до 100.\n Попробуй снова.")
        return
    if not 0 <= score <= 100:
        bot.send_message(chat_id, "Не подходящий формат. Баллы должны быть введены числом от 0 до 100\n Попробуй снова.")
        return
    session = Session()
    existing_student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
    existing_score = session.query(Score).filter_by(student_id=existing_student.id, subject=subject).first()
    if existing_score:
        existing_score.score = score
    else:
        new_score = Score(subject=subject, score=score, student=existing_student)
        session.add(new_score)
    session.commit()
    session.close()
    bot.send_message(chat_id, "Баллы ЕГЭ успешно сохранены!")


@bot.message_handler(commands=['view_scores'])
def handle_view_scores(message):
    chat_id = message.chat.id
    session = Session()
    existing_student = session.query(Student).filter_by(telegram_id=message.from_user.id).first()
    if not existing_student:
        bot.send_message(chat_id, 'Тебе нужно зарегистрироваться и внести свои баллы.')
        session.close()
        return
    if not existing_student.scores:
        bot.send_message(chat_id, 'Тебе нужно внести свои баллы.')
        session.close()
        return
    scores_text = "Твои сохраненные баллы ЕГЭ:\n"
    for score_entry in existing_student.scores:
        scores_text += f"{score_entry.subject.capitalize()}: {score_entry.score}\n"
    bot.send_message(chat_id, scores_text)
    session.close()


@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = """
    Доступные команды:
    /start - Начать работу с ботом
    /register - Зарегистрироваться или обновить информацию о себе
    /enter_scores - Ввести свои баллы ЕГЭ
    /view_scores - Просмотреть свои сохраненные баллы ЕГЭ
    /help - Показать список доступных команд
    """
    bot.send_message(message.chat.id, help_text)