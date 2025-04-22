import json
import os
import threading
import time
import requests
import telebot
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging
from const import NOTICE_URL, headers, notice_save, user_save


log_format = "%(levelname)s - %(asctime)s - %(message)s"
date_format = "%d/%m/%y %H:%M:%S"

# Set up logger
logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    datefmt=date_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)


load_dotenv()
first_run = True

bot = telebot.TeleBot(os.getenv("TOKEN"))


def get_last_notice() -> tuple[str, str]:
    res = requests.get(NOTICE_URL, headers=headers)
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        notice = soup.select_one("td.content-left")
        link = notice.find("a")
        notice_file_url = link.get("href")
        notice_title = link.get_text(strip=True)
        return notice_title, notice_file_url
    

def scrape_all_notice() -> list:
    res = requests.get(NOTICE_URL, headers=headers)
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        logging.info("Scraped all notice")
        return soup.select("td.content-left")
    

def save_all_notice(notices: list):
    notice_urls = []
    for notice in notices:
        link = notice.find("a")
        if link and link.get("href"):
            notice_urls.append(link.get("href"))
    with open(notice_save, 'w') as f:
        json.dump(notice_urls, f)


def get_all_notice() -> list[str]:
    with open(notice_save, 'r') as f:
        notice_urls = json.load(f)
    return notice_urls


def get_user_ids() -> list[int]:
    try:
        with open(user_save, 'r') as f:
            user_ids = json.load(f)
    except FileNotFoundError:
        user_ids = []
    return user_ids


def save_user_ids(ids: list[int]):
    with open(user_save, 'w') as f:
        json.dump(ids, f)


def download_file(url: str, destination_folder: str ='.') -> str|None:
    filename = os.path.basename(url)
    file_path = os.path.join(destination_folder, filename)
    if os.path.exists(file_path):
        return filename
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        logging.debug(f"Downloaded file {filename}")
        return filename
    except Exception:
        return None
    

def send_notice(user_id: int, message: str, filename: str):
    try:
        with open(filename, 'rb') as doc:
            bot.send_document(user_id, doc, caption=message)
            logging.debug(f"sent notice to user {user_id}")
    except telebot.apihelper.ApiException as e:
        if e.error_code == 403:
            logging.info(f"User {user_id} has blocked the bot.")
            user_ids = get_user_ids()
            user_ids.remove(user_id)
            logging.debug(f"Removed user {user_id} from list")
            save_user_ids(user_ids)
        else:
            logging.error(f"Failed to send document to {user_id}: {e}")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_ids = get_user_ids()
    if user_id not in user_ids:
        user_ids.append(user_id)
        logging.debug(f"Added user id {user_id} to the list")
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


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "/last - To get the last notice\nOther than that, notices will be sent automatically\n\nFor any kind of information, inquiry or report please contact @faridinqn")

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
                        logging.debug(f"Removed file {fname}")
        time.sleep(7 * 60)


if __name__ == "__main__":
    threading.Thread(target=check_notice, daemon=True).start()
    bot.infinity_polling()