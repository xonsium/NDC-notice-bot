from const import NOTICE_URL, headers, notice_save, user_save
import json
import requests
from bs4 import BeautifulSoup
import os
from logger_config import logger

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
        logger.info("Scraped all notice")
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
        logger.debug(f"Downloaded file {filename}")
        return filename
    except Exception:
        return None
