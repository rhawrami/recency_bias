"""Build Game Awards nominations (2014–2025) from annual ceremony tables.

Source pages are community-maintained Wikipedia lists; official TGA winner
pages are downloaded independently to make discrepancies visible.
"""

import csv
import datetime as dt
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
YEARS = range(2014, 2026)
USER_AGENT = "RecencyBiasResearch/0.1 (academic research; https://github.com/)"
SPACE = re.compile(r"\s+")


def fetch(url):
    for attempt in range(6):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read().decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 5:
                raise
            time.sleep(2 ** attempt + 2)


def tidy(text):
    return SPACE.sub(" ", text.replace("\xa0", " ")).strip()


def write_csv(name, records, columns):
    DATA.mkdir(exist_ok=True)
    with (DATA / name).open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def label(th):
    # Inline footnote markers are editorial, not part of a category's name.
    fragment = BeautifulSoup(str(th), "html.parser")
    for ref in fragment.select("sup.reference, style, link"):
        ref.decompose()
    return tidy(fragment.get_text(" ", strip=True))


def category_type(name, section):
    lower = name.casefold()
    if section == "honorary" or "icon" in lower or "game changer" in lower:
        return "honorary"
    if "adaptation" in lower:
        return "adaptation"
    if "anticipated" in lower:
        return "unreleased_game"
    if "performance" in lower:
        return "performance"
    if any(word in lower for word in ("athlete", "esports player", "player of the year", "coach", "creator", "gamer", "esports host")):
        return "person"
    if any(word in lower for word in ("esports team", "esports event", "esports moment",
                                      "developer of the year", "fan creation", "citizens")):
        return "other"
    return "game"


def nominees_in_cell(cell, category, section):
    outer = cell.find(["ul", "ol"])
    if not outer:
        raise ValueError(f"No nominee list for {category}")
    first = outer.find("li", recursive=False)
    if not first:
        raise ValueError(f"Empty nominee list for {category}")
    nested = first.find(["ul", "ol"], recursive=False)
    entries = [first] + (nested.find_all("li", recursive=False) if nested else outer.find_all("li", recursive=False)[1:])
    kind = category_type(category, section)
    result = []
    for index, entry in enumerate(entries):
        item = BeautifulSoup(str(entry), "html.parser").li
        for nested_list in item.find_all(["ul", "ol"]):
            nested_list.decompose()
        for sup in item.select("sup.reference"):
            sup.decompose()
        raw = tidy(item.get_text(" ", strip=True)).rstrip("‡ ")
        # Nominee identity precedes the producer/credit separator. An em dash
        # inside a name is preserved; the source tables use an en dash here.
        name = tidy(re.split(r"\s+[–—]\s+", raw, maxsplit=1)[0])
        italic = item.find(["i", "em"])
        game = ""
        link = ""
        if kind in ("game", "unreleased_game", "performance"):
            if italic:
                game = tidy(italic.get_text(" ", strip=True))
                anchor = italic.find("a", href=True)
            elif kind == "game":
                game = name
                anchor = item.find("a", href=True)
            else:
                anchor = None
            if anchor and anchor["href"].startswith("/wiki/"):
                link = urllib.parse.urljoin("https://en.wikipedia.org", anchor["href"].split("#")[0])
        result.append({
            "nominee": name,
            "game_title": game,
            "game_wikipedia_url": link,
            "is_winner": 1 if index == 0 or kind == "honorary" else 0,
            "nominee_order": index + 1,
            "raw_nomination": raw,
        })
    return result


def awards_from_wikipedia(year):
    page_url = f"https://en.wikipedia.org/wiki/The_Game_Awards_{year}"
    api = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "parse", "page": f"The_Game_Awards_{year}", "prop": "text", "format": "json"
    })
    response = json.loads(fetch(api))["parse"]
    soup = BeautifulSoup(response["text"]["*"], "html.parser")
    categories, nominations = [], []
    for table in soup.select("table.wikitable"):
        # Summary tables further down the page are NOT award categories.
        if not table.select_one("tr > th") or label(table.select_one("tr > th")).startswith(("Nominations", "Awards")):
            break
        heading = table.find_previous(re.compile("^h[234]$"))
        section_text = heading.get_text(" ", strip=True).casefold() if heading else ""
        if "honorary" in section_text:
            section = "honorary"
        elif "fan-voted" in section_text:
            section = "fan-voted"
        else:
            section = "standard"
        for row in table.select("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            if not cells or cells[0].name != "th":
                continue
            nominees_row = row.find_next_sibling("tr")
            if not nominees_row:
                raise ValueError(f"Missing nominee row for {year}: {label(cells[0])}")
            nominee_cells = nominees_row.find_all("td", recursive=False)
            if len(cells) != len(nominee_cells):
                raise ValueError(f"Category/nominee count differs for {year}: {label(cells[0])}")
            for th, cell in zip(cells, nominee_cells):
                name = label(th)
                category_id = f"{year}-{len(categories) + 1:02}"
                kind = category_type(name, section)
                categories.append({"category_id": category_id, "year": year,
                                   "category": name, "category_type": kind,
                                   "section": section, "source_url": page_url})
                for entry in nominees_in_cell(cell, name, section):
                    nominations.append({"nomination_id": f"{category_id}-{entry['nominee_order']:02}",
                                        "category_id": category_id, "year": year,
                                        "category": name, "category_type": kind,
                                        "nomination_status": ("withdrawn" if year == 2025 and
                                                              name == "Best Debut Indie Game" and
                                                              entry["nominee"] == "Megabonk" else "active"),
                                        "source_url": page_url, **entry})
    if len(categories) < 15 or len(nominations) < 70:
        raise ValueError(f"Implausible coverage for {year}: {len(categories)} categories, {len(nominations)} nominees")
    return categories, nominations, response.get("revid")


def official_rewind(year):
    url = f"https://thegameawards.com/rewind/year-{year}"
    soup = BeautifulSoup(fetch(url), "html.parser")
    header = soup.find("h2", string=re.compile(r"^Winners$", re.I))
    if not header:
        raise ValueError(f"Official Rewind missing winners: {url}")
    result = []
    # Headings between the Winners heading and the footer are repeating h2/h3/h4.
    for h2 in header.find_all_next("h2"):
        if h2.get_text(" ", strip=True).casefold() in ("sign in", "my badges"):
            break
        h3 = h2.find_next("h3")
        if h3 and h3.find_previous("h2") != h2:
            continue
        if h3:
            result.append({"year": year, "category": tidy(h2.get_text(" ", strip=True)),
                           "winner": tidy(h3.get_text(" ", strip=True)), "source_url": url})
    return result


def official_2025_categories():
    index_url = "https://thegameawards.com/nominees/game-of-the-year"
    soup = BeautifulSoup(fetch(index_url), "html.parser")
    slugs = sorted({a["href"] for a in soup.select('a[href^="/nominees/"]')
                    if a["href"].count("/") == 2})
    if len(slugs) < 25:
        raise ValueError(f"Expected 2025 official category links, found {len(slugs)}")
    result, nominees = [], []
    for slug in slugs:
        url = urllib.parse.urljoin("https://thegameawards.com", slug)
        page = BeautifulSoup(fetch(url), "html.parser")
        badge = page.find(string=lambda text: text and text.strip() == "Winner")
        winner = badge.find_next("h3") if badge else None
        if not winner:
            raise ValueError(f"Cannot identify 2025 winner from {url}")
        category_name = slug.rsplit("/", 1)[-1].replace("-", " ").title()
        result.append({"year": 2025, "category": category_name,
                       "winner": tidy(winner.get_text(" ", strip=True)), "source_url": url})
        for badge in page.find_all(string=lambda text: text and text.strip() in ("Winner", "Voting Closed")):
            h3 = badge.find_next("h3")
            if h3 and h3.find_previous(string=lambda text: text and text.strip() in ("Winner", "Voting Closed")) == badge:
                nominees.append({"year": 2025, "category": category_name,
                                 "nominee": tidy(h3.get_text(" ", strip=True)),
                                 "is_winner": int(badge.strip() == "Winner"), "source_url": url})
        time.sleep(0.8)
    return result, nominees


def main():
    categories, nominations, revisions, official = [], [], [], []
    for year in YEARS:
        year_categories, year_nominations, revid = awards_from_wikipedia(year)
        categories.extend(year_categories)
        nominations.extend(year_nominations)
        revisions.append({"year": year, "wikipedia_revision": revid,
                          "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
        print(f"{year}: {len(year_categories)} categories, {len(year_nominations)} nominees", flush=True)
        time.sleep(1.5)
    # Game Changer is honorary and was described in prose, not the nominee
    # tables, in the 2024 and 2025 ceremony articles.
    for year, recipient in ((2024, "Amir Satvat"), (2025, "Girls Make Games")):
        category_id = f"{year}-{1 + sum(c['year'] == year for c in categories):02}"
        url = f"https://en.wikipedia.org/wiki/The_Game_Awards_{year}"
        categories.append({"category_id": category_id, "year": year,
                           "category": "Game Changer", "category_type": "honorary",
                           "section": "honorary", "source_url": url})
        nominations.append({"nomination_id": f"{category_id}-01", "category_id": category_id,
                            "year": year, "category": "Game Changer", "category_type": "honorary",
                            "nominee": recipient, "game_title": "", "game_wikipedia_url": "",
                            "is_winner": 1, "nominee_order": 1, "raw_nomination": recipient,
                            "nomination_status": "active",
                            "source_url": url})
    for year in range(2014, 2025):
        official.extend(official_rewind(year))
        time.sleep(1)
    official_2025, official_nominees_2025 = official_2025_categories()
    official.extend(official_2025)
    voice = BeautifulSoup(fetch("https://thegameawards.com/brackets/players-voice"), "html.parser")
    badge = voice.find(string=lambda text: text and text.strip() == "Winner")
    if not badge or not badge.find_next("h3"):
        raise ValueError("Cannot identify official 2025 Players' Voice winner")
    official.append({"year": 2025, "category": "Players' Voice",
                     "winner": tidy(badge.find_next("h3").get_text(" ", strip=True)),
                     "source_url": "https://thegameawards.com/brackets/players-voice"})
    for status in voice.find_all(string=lambda text: text and text.strip() in ("Winner", "Voting Closed")):
        h3 = status.find_next("h3")
        if h3 and h3.find_previous(string=lambda text: text and text.strip() in ("Winner", "Voting Closed")) == status:
            official_nominees_2025.append({"year": 2025, "category": "Players' Voice",
                                           "nominee": tidy(h3.get_text(" ", strip=True)),
                                           "is_winner": int(status.strip() == "Winner"),
                                           "source_url": "https://thegameawards.com/brackets/players-voice"})
    # 2025 Rewind currently returns 404; the official site has 2025 category
    # pages, while Wikipedia supplies the full 2025 nomination list above.
    write_csv("categories.csv", categories, ["category_id", "year", "category", "category_type", "section", "source_url"])
    write_csv("nominations.csv", nominations, ["nomination_id", "category_id", "year", "category", "category_type", "nominee", "game_title", "game_wikipedia_url", "is_winner", "nominee_order", "nomination_status", "raw_nomination", "source_url"])
    write_csv("official_winners.csv", official, ["year", "category", "winner", "source_url"])
    write_csv("official_nominees_2025.csv", official_nominees_2025,
              ["year", "category", "nominee", "is_winner", "source_url"])
    write_csv("source_revisions.csv", revisions, ["year", "wikipedia_revision", "retrieved_utc"])
    print(f"Total: {len(categories)} categories, {len(nominations)} nominations, {len(official)} official winners")


if __name__ == "__main__":
    main()
