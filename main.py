import json
from logging import basicConfig, info, warning
from os import environ

import requests
from bs4 import BeautifulSoup


basicConfig(format='%(asctime)s: %(message)s')


class Result:
    def __init__(self, lastPage: bool, html: str):
        self.last_page = lastPage
        self.html = html


class Race:
    def __init__(self, date: str, time: str, location: str):
        self.date = date
        self.time = time
        self.location = location


def get_url(offset=0, total_item_loaded=8):
    return f"https://www.nyrr.org/api/feature/volunteer/FilterVolunteerOpportunities?available_only=true&" \
           f"itemId=3EB6F0CC-0D76-4BAF-A894-E2AB244CEB44&limit=8&offset={offset}&totalItemLoaded={total_item_loaded}"


def extract_info(element, key):
    return element.find("div", {"class": f"role_listing__{key}"}).text


def extract_races(offset=0):
    content = requests.get(get_url(offset=offset)).content
    try:
        raw = json.loads(content)
    except json.decoder.JSONDecodeError:
        warning("Failed to get content")
        raw = {"lastPage": True, "html": ""}
        
    raw = Result(**raw)
    possibilities = []
    races = BeautifulSoup(raw.html).find_all("section", {"class": "role_listing"})
    for r in races:
        if r.find("div", {"class": "tag tag--no"}) and r.find("div", {"class": "tag tag--no"}).text == ' 9+1 ':
            continue  # Does not count for 9 + 1
        if r.find("div", {"class": "medical_icon"}):
            continue  # Medical volunteer only
        possibilities.append(Race(**{e: extract_info(r, e) for e in ["date", "time", "location"]}))

    return raw.last_page, possibilities


def send_text(bot_message):
    if not environ.get("TELEGRAM_TOKEN") or not environ.get("TELEGRAM_HASH"):
        info("Telegram not setup")

    requests.get(f'https://api.telegram.org/bot{environ.get("TELEGRAM_TOKEN")}/sendMessage?chat_id='
                 f'{environ.get("TELEGRAM_HASH")}&parse_mode=Markdown&text={bot_message}')


def run():
    warning("Bot starting")
    last_page, races, offset = False, [], 0
    while not last_page:
        last_page, items = extract_races(offset)
        races.extend(items)
        offset += 8
    if races:
        info(f"Found {len(races)} options")
        for r in races:
            send_text(f"Race : {r.date} {r.time} at {r.location}")
    send_text(f"Race : This is a test")


if __name__ == "__main__":
    run()
