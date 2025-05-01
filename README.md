# NDC Notice Bot

Fetches new notice from https://ndc.edu.bd/ and automatically sends it to all users that have added the bot.

## Installation
```
pip install -r requirements.txt
python3 main.py
```


## Add the bot
[@NDCNoticeBot](https://t.me/NDCNoticeBot)

## Usage
- /start - Adds you to users list
- /last - gives you the last notice
- list - gives you the last 6 notice to choose from

Libraries: 
- pyTelegramBotAPI
- requests
- selectolax or bs4
- python-dotenv