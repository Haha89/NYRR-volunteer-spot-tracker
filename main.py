import json
from os import environ
from typing import List

import requests
from bs4 import BeautifulSoup


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
    print(f"Fetching races with offset {offset}")
    return f"https://www.nyrr.org/api/feature/volunteer/FilterVolunteerOpportunities?available_only=true&" \
           f"itemId=3EB6F0CC-0D76-4BAF-A894-E2AB244CEB44&limit={total_item_loaded}&offset={offset}&totalItemLoaded={total_item_loaded}"


def extract_info(element, key):
    return element.find("div", {"class": f"role_listing__{key}"}).text


def extract_races(offset=0) -> (bool, List[Race], int):
    content = requests.get(get_url(offset=offset)).content
    try:
        raw = json.loads(content)
    except json.decoder.JSONDecodeError:
        print(f"Failed to convert content: {content}")
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

    return raw.last_page, possibilities, len(races)


def send_text(bot_message):
    if not environ.get("TELEGRAM_TOKEN") or not environ.get("TELEGRAM_HASH"):
        print("Telegram not setup")

    return requests.get(f'https://api.telegram.org/bot{environ.get("TELEGRAM_TOKEN")}/sendMessage?chat_id='
                        f'{environ.get("TELEGRAM_HASH")}&parse_mode=Markdown&text={bot_message}')


def run():
    print("Bot starting")
    last_page, races, offset = False, [], 0
    while not last_page:
        last_page, items, nb_races = extract_races(offset)
        races.extend(items)
        offset += nb_races

    for r in races:
        send_text(f"Race : {r.date} {r.time} at {r.location}")


if __name__ == "__main__":
    run()
