#!/usr/bin/env PYTHONIOENCODING=UTF-8 /usr/local/bin/python3
import json
import subprocess
from typing import List, Iterator, Iterable, Tuple
import xml.etree.ElementTree as ETree

import requests
import requests.auth


GMAIL_USER = "you gmail username"
GMAIL_PASSWORD = "your gmail app specific password"


def get_xml() -> ETree.Element:
    feed = requests.get(
        "https://mail.google.com/mail/feed/atom",
        auth=requests.auth.HTTPBasicAuth(GMAIL_USER, GMAIL_PASSWORD),
    )
    feed.raise_for_status()
    return ETree.fromstring(feed.text)


def get_text(elt: ETree.Element, tag: str) -> str:
    t = elt.find(tag)
    if t is None:
        return ""
    else:
        return t.text or ""


def get_ids(xml: ETree.Element) -> Iterator[Tuple[str, str, str, str]]:
    for entry in xml.findall(".//{http://purl.org/atom/ns#}entry"):
        title = get_text(entry, "{http://purl.org/atom/ns#}title")
        summary = get_text(entry, "{http://purl.org/atom/ns#}summary")
        author = get_text(
            entry,
            "{http://purl.org/atom/ns#}author/{http://purl.org/atom/ns#}name",
        )
        the_id = get_text(entry, "{http://purl.org/atom/ns#}id")
        yield (the_id, title, summary, author)


def get_shown() -> Iterable[str]:
    try:
        with open("/tmp/shown.json") as f:
            shown = json.load(f)
            assert isinstance(shown, list)
            return shown
    except FileNotFoundError:
        return []


def save_shown(ids: List[str]) -> None:
    with open("/tmp/shown.json", "w") as f:
        json.dump(ids, f)


# noinspection PyUnusedLocal
def notify(title: str, summary: str, author: str) -> None:
    subprocess.run(
        [
            "/usr/local/bin/terminal-notifier",
            "-message",
            title,
            "-title",
            author,
        ]
    )


def main():
    status = "📬"
    shown = get_shown()
    # noinspection PyBroadException
    try:
        ids = list(get_ids(get_xml()))
    except requests.exceptions.ConnectionError:
        print(f"{status} .")
        return
    except Exception:
        print(f"{status} !")
        return

    def f():
        for an_id, title, summary, author in ids:
            if an_id not in shown:
                notify(title, summary, author)
            yield an_id

    save_shown(list(f()))

    n = len(ids)
    if n > 0:
        status += f" {n}"

    print(f"{status}|color=green")


if __name__ == "__main__":
    main()
