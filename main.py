import os
import threading
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from logger_config import logger
from utils import *


load_dotenv()
first_run = True

bot = telebot.TeleBot(os.getenv("TOKEN"))

def send_notice(user_id: int, message: str, filename: str):
    try:
        with open(filename, 'rb') as doc:
            bot.send_document(user_id, doc, caption=message)
            logger.debug(f"sent notice to user {user_id}")
    except telebot.apihelper.ApiException as e:
        if e.error_code == 403:
            logger.info(f"User {user_id} has blocked the bot.")
            user_ids = get_user_ids()
            user_ids.remove(user_id)
            logger.debug(f"Removed user {user_id} from list")
            save_user_ids(user_ids)
        else:
            logger.error(f"Failed to send document to {user_id}: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_ids = get_user_ids()
    if user_id not in user_ids:
        user_ids.append(user_id)
        logger.debug(f"Added user id {user_id} to the list")
        save_user_ids(user_ids)
        bot.reply_to(message, "Welcome! You've been added to the users list.")
        title, file_url = get_last_notice()
        if os.path.splitext(file_url)[-1] == "":
            bot.reply_to(message, f"Last Notice: {title} \n {file_url}")
        else:
            fname = download_file(file_url)
            if fname:
                msg = f"Last Notice: {title}"
                send_notice(user_id, msg, fname)
    else:
        bot.reply_to(message, "You are already in the users list. You'll be sent the notice as soon as it has been published in the college website.")    


@bot.message_handler(commands=['last'])
def send_welcome(message):
    user_id = message.chat.id
    title, file_url = get_last_notice()
    if os.path.splitext(file_url)[-1] == "":
        bot.reply_to(message, f"Last Notice: {title} \n {file_url}")
    else:
        fname = download_file(file_url)
        if fname:
            msg = f"Last Notice: {title}"
            send_notice(user_id, msg, fname)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data.split("|")
    file_url = "https://ndc.edu.bd/storage/app/uploads/public" + data[-1]
    if data[0] == "send_notice":
        bot.answer_callback_query(call.id, "Sending Notice")

        if os.path.splitext(file_url)[-1] == "":
            bot.reply_to(call.message.chat.id, f"Notice: \n {file_url}")
        else:
            fname = download_file(file_url)
            if fname:
                msg = f"Notice"
                send_notice(call.message.chat.id, msg, fname)

@bot.message_handler(commands=['list'])
def send_list(message):
    notices = scrape_all_notice()[0:6]
    keyboard = InlineKeyboardMarkup()
    keyboard.row_width = 2
    for i, notice in enumerate(notices):
        a_tag = notice.find('a')
        href = a_tag['href']
        link_part = href.split('public')[-1]
        title = a_tag.text
        title = f"{title[0:25]}..."
        keyboard.add(
            InlineKeyboardButton(title, callback_data=f"send_notice|{link_part}")
        )
    bot.send_message(message.chat.id, "Choose a notice", reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "/last - gives you the last notice\n/list - gives you the last 6 notice to choose from\nOther than that, notices will be sent automatically\n\nFor any kind of information, inquiry or report please contact @faridinqn")

def check_notice():
    global first_run
    while True:
        notices = scrape_all_notice()
        if first_run:
            save_all_notice(notices)
            first_run = False
        else:
            saved_notices = get_all_notice()
            for notice in notices:
                link = notice.find("a")
                if not link:
                    continue
                file_url = link.get("href")
                if file_url not in saved_notices:
                    if os.path.splitext(file_url)[-1] == "":
                        for user_id in user_ids:
                            bot.reply_to(user_id, f"Last Notice: {title} \n {file_url}")
                    else:
                        title = link.get_text(strip=True)
                        fname = download_file(file_url)
                        msg = f"Latest Notice: {title}"
                        user_ids = get_user_ids()
                        for user_id in user_ids:
                            send_notice(user_id, msg, fname)
                        save_all_notice(notices)
                        os.remove(fname)
                        logger.debug(f"Removed file {fname}")
        time.sleep(7 * 60)


if __name__ == "__main__":
    threading.Thread(target=check_notice, daemon=True).start()
    bot.infinity_polling()