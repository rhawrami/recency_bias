"""Resolve nominated games to Wikidata and retain every dated release claim.

The earliest date is an ORIGINAL release, not necessarily the qualifying
release for an award (ports, regional launches, early access, DLC, seasons).
"""

import csv
import json
import time
import urllib.error
import urllib.parse

from build_awards import DATA, fetch, write_csv


def batches(values, size=40):
    for start in range(0, len(values), size):
        yield values[start:start + size]


def api(host, parameters):
    path = "/sparql" if "query.wikidata.org" in host else "/w/api.php"
    return json.loads(fetch(host + path + "?" + urllib.parse.urlencode(parameters)))


def wiki_title(url):
    return urllib.parse.unquote(url.partition("/wiki/")[2]).replace("_", " ")


def normalize_date(value, precision):
    # Wikidata precision 11 = day, 10 = month, 9 = year.
    match = value[1:11]
    if int(precision) >= 11:
        return match, "day"
    if int(precision) == 10:
        return match[:7], "month"
    if int(precision) == 9:
        return match[:4], "year"
    return "", "less_than_year"


# These are documented award-year releases that differ from the title's
# earliest worldwide public launch; other cross-year cases remain unresolved.
AWARD_YEAR_RELEASES = {
    (2014, "Bravely Default"): ("2014-02-07", "North American release of For the Sequel edition",
                                "https://en.wikipedia.org/wiki/Bravely_Default#Release"),
    (2014, "Grand Theft Auto V"): ("2014-11-18", "PS4/Xbox One remaster release",
                                  "https://en.wikipedia.org/wiki/Grand_Theft_Auto_V"),
    (2014, "Killer Instinct: Season Two"): ("2014-10-15", "Season Two launch, not the 2013 base game",
                                            "https://en.wikipedia.org/wiki/Killer_Instinct_(2013_video_game)"),
    (2014, "Persona 4 Arena Ultimax"): ("2014-08-28", "first console launch, after 2013 Japanese arcade release",
                                        "https://en.wikipedia.org/wiki/Persona_4_Arena_Ultimax"),
    (2014, "Ultra Street Fighter IV"): ("2014-06-03", "Ultra update on consoles, not the 2008 base game",
                                         "https://en.wikipedia.org/wiki/Ultra_Street_Fighter_IV"),
    (2017, "Persona 5"): ("2017-04-04", "worldwide release after 2016 Japanese launch",
                         "https://en.wikipedia.org/wiki/Persona_5"),
    (2019, "Beat Saber"): ("2019-05-21", "full release after early access",
                           "https://en.wikipedia.org/wiki/Beat_Saber"),
    (2020, "Hades"): ("2020-09-17", "full release after 2018 early access",
                      "https://en.wikipedia.org/wiki/Hades_(video_game)"),
    (2021, "Resident Evil 4"): ("2021-10-21", "Oculus Quest 2 VR edition",
                               "https://en.wikipedia.org/wiki/Resident_Evil_4"),
    (2023, "Resident Evil Village"): ("2023-02-22", "PlayStation VR2 mode",
                                     "https://en.wikipedia.org/wiki/Resident_Evil_Village"),
    (2023, "Gran Turismo 7"): ("2023-02-22", "PlayStation VR2 availability",
                                 "https://blog.playstation.com/2023/02/20/gran-turismo-7-update-1-29-includes-ps-vr2-upgrade-a-race-against-superhuman-ai-a-classic-gt-track-and-5-new-cars/"),
    (2024, "Arizona Sunshine Remake"): ("2024-10-17", "VR remake launch, not the 2016 base game",
                                        "https://en.wikipedia.org/wiki/Arizona_Sunshine"),
    (2023, "Baldur's Gate 3"): ("2023-08-03", "full PC release after early access",
                                 "https://www.wikidata.org/wiki/Q64441774#P577"),
    (2025, "Hades II"): ("2025-09-25", "full release after early access",
                           "https://www.wikidata.org/wiki/Q115641620#P577"),
    (2025, "Umamusume: Pretty Derby"): ("2025-06-26", "worldwide English-language mobile release",
                                       "https://en.wikipedia.org/wiki/Umamusume:_Pretty_Derby"),
}

# These documented initial launches or early-access dates are missing or
# misidentified in the earliest Wikidata release claims. Bayonetta 2's
# February 13, 2014 P577 claim is a pre-release Nintendo Direct; KOF XIV and
# Iceborne have later PC dates despite earlier console launches.
ORIGINAL_RELEASE_CORRECTIONS = {
    "Bayonetta 2": ("2014-09-20", "https://en.wikipedia.org/wiki/Bayonetta_2"),
    "Super Smash Bros. for Nintendo 3DS": ("2014-09-13", "https://en.wikipedia.org/wiki/Super_Smash_Bros._for_Nintendo_3DS_and_Wii_U"),
    "Block'hood": ("2016-03-10", "https://en.wikipedia.org/wiki/Block%27hood#Development"),
    "The King of Fighters XIV": ("2016-08-23", "https://en.wikipedia.org/wiki/The_King_of_Fighters_XIV"),
    "Valiant Hearts: The Great War": ("2014-06-25", "https://en.wikipedia.org/wiki/Valiant_Hearts:_The_Great_War"),
    "Overcooked 2": ("2018-08-07", "https://en.wikipedia.org/wiki/Overcooked_2"),
    "Beat Saber": ("2018-05-01", "https://en.wikipedia.org/wiki/Beat_Saber"),
    "Rez Infinite": ("2016-10-13", "https://en.wikipedia.org/wiki/Rez#Rez_Infinite"),
    "Nier Replicant ver 1.22474487139": ("2021-04-22", "https://en.wikipedia.org/wiki/Nier_(video_game)#Remaster"),
    "Monster Hunter World: Iceborne": ("2019-09-06", "https://en.wikipedia.org/wiki/Monster_Hunter_World:_Iceborne"),
    "Umamusume: Pretty Derby": ("2021-02-24", "https://en.wikipedia.org/wiki/Umamusume:_Pretty_Derby"),
}


def main():
    with (DATA / "nominations.csv").open(encoding="utf-8", newline="") as stream:
        nominations = list(csv.DictReader(stream))
    links = sorted({row["game_wikipedia_url"] for row in nominations if row["game_wikipedia_url"]})
    title_to_qid = {}
    entities = {}
    checkpoint = DATA / ".release_lookup.json"
    if checkpoint.exists():
        saved = json.loads(checkpoint.read_text(encoding="utf-8"))
        title_to_qid.update(saved["title_to_qid"])
        entities.update(saved["entities"])
    remaining = [link for link in links if link not in title_to_qid]
    for index, chunk in enumerate(batches(remaining, 50)):
        values = " ".join("<" + link + ">" for link in chunk)
        query = ("SELECT ?article ?item ?date ?precision ?statement WHERE { "
                 f"VALUES ?article {{ {values} }} "
                 "?article <http://schema.org/about> ?item . "
                 "OPTIONAL { ?item p:P577 ?statement . ?statement psv:P577 ?timeNode . "
                 "?timeNode wikibase:timeValue ?date ; wikibase:timePrecision ?precision . } }")
        result = api("https://query.wikidata.org", {"query": query, "format": "json"})
        for binding in result["results"]["bindings"]:
            link = binding["article"]["value"]
            qid = binding["item"]["value"].rsplit("/", 1)[-1]
            title_to_qid[link] = qid
            entity = entities.setdefault(qid, {"claims": {"P577": []}})
            if "date" in binding:
                date = binding["date"]["value"]
                entity["claims"]["P577"].append({
                    "id": binding["statement"]["value"].rsplit("/", 1)[-1],
                    "mainsnak": {"snaktype": "value", "datavalue": {"value": {
                        "time": "+" + date, "precision": int(binding["precision"]["value"])
                    }}}
                })
        for link in chunk:
            title_to_qid.setdefault(link, "")
        checkpoint.write_text(json.dumps({"title_to_qid": title_to_qid,
                                          "entities": entities}), encoding="utf-8")
        print(f"Wikidata release batch {index + 1}; {len(title_to_qid)}/{len(links)} links", flush=True)
        time.sleep(3)

    # Some ceremony tables link to a Wikipedia redirect (e.g. Helldivers II
    # -> Helldivers 2); WDQS stores only the canonical sitelink.
    missing = [link for link in links if not title_to_qid.get(link)]
    for chunk in batches(missing, 8):
        titles = [wiki_title(link) for link in chunk]
        try:
            result = api("https://en.wikipedia.org", {
                "action": "query", "prop": "pageprops", "ppprop": "wikibase_item",
                "redirects": "1", "titles": "|".join(titles), "format": "json"
            })["query"]
        except urllib.error.HTTPError as exc:
            if exc.code != 429:
                raise
            print(f"Rate-limited resolving {len(chunk)} redirects; leave undated", flush=True)
            continue
        aliases = {entry["from"]: entry["to"] for entry in
                   result.get("normalized", []) + result.get("redirects", [])}
        canonical = {p["title"]: p.get("pageprops", {}).get("wikibase_item", "")
                     for p in result["pages"].values()}
        for link, title in zip(chunk, titles):
            target = title
            for _ in range(4):
                target = aliases.get(target, target)
            title_to_qid[link] = canonical.get(target, "")
        time.sleep(3)
    new_ids = sorted(set(title_to_qid.values()) - set(entities) - {""})
    for chunk in batches(new_ids, 50):
        values = " ".join("wd:" + qid for qid in chunk)
        query = ("SELECT ?item ?date ?precision ?statement WHERE { "
                 f"VALUES ?item {{ {values} }} "
                 "OPTIONAL { ?item p:P577 ?statement . ?statement psv:P577 ?timeNode . "
                 "?timeNode wikibase:timeValue ?date ; wikibase:timePrecision ?precision . } }")
        result = api("https://query.wikidata.org", {"query": query, "format": "json"})
        for binding in result["results"]["bindings"]:
            qid = binding["item"]["value"].rsplit("/", 1)[-1]
            entity = entities.setdefault(qid, {"claims": {"P577": []}})
            if "date" in binding:
                entity["claims"]["P577"].append({
                    "id": binding["statement"]["value"].rsplit("/", 1)[-1],
                    "mainsnak": {"snaktype": "value", "datavalue": {"value": {
                        "time": "+" + binding["date"]["value"],
                        "precision": int(binding["precision"]["value"])
                    }}}
                })
    checkpoint.write_text(json.dumps({"title_to_qid": title_to_qid,
                                      "entities": entities}), encoding="utf-8")

    events = []
    for link in links:
        qid = title_to_qid.get(link, "")
        for statement in entities.get(qid, {}).get("claims", {}).get("P577", []):
            snak = statement["mainsnak"]
            if snak.get("snaktype") != "value":
                continue
            value = snak["datavalue"]["value"]
            date, precision = normalize_date(value["time"], value["precision"])
            if not date or value["time"].startswith("-"):
                continue
            def qualifier_ids(property_id):
                return "|".join(str(q.get("datavalue", {}).get("value", {}).get("id", ""))
                                for q in statement.get("qualifiers", {}).get(property_id, []))
            events.append({"game_wikipedia_url": link, "wikidata_id": qid,
                           "release_date": date, "date_precision": precision,
                           "platform_ids": qualifier_ids("P400"),
                           "place_ids": qualifier_ids("P291"),
                           "statement_id": statement.get("id", ""),
                           "source_url": f"https://www.wikidata.org/wiki/{qid}#P577"})
    events.sort(key=lambda e: (e["game_wikipedia_url"],
                               {"day": 0, "month": 1, "year": 2}.get(e["date_precision"], 3),
                               e["release_date"]))
    first = {}
    for event in events:
        first.setdefault(event["game_wikipedia_url"], event)

    for row in nominations:
        link = row["game_wikipedia_url"]
        event = first.get(link, {})
        correction = ORIGINAL_RELEASE_CORRECTIONS.get(row["game_title"])
        award = AWARD_YEAR_RELEASES.get((int(row["year"]), row["game_title"]))
        first_date = correction[0] if correction else event.get("release_date", "")
        first_source = correction[1] if correction else event.get("source_url", "")
        precision = "day" if correction else event.get("date_precision", "")
        candidate = (award[0] if award else first_date
                     if precision == "day" and first_date.startswith(row["year"] + "-") else "")
        row.update({"wikidata_id": title_to_qid.get(link, ""),
                    "original_release_date": first_date,
                    "original_release_precision": precision,
                    "release_source_url": first_source,
                    "award_year_release_date": candidate,
                    "award_year_release_basis": (award[1] if award else "first public release" if candidate else ""),
                    "award_year_release_source_url": (award[2] if award else first_source if candidate else ""),
                    "release_date_status": ("no_associated_game" if not row["game_title"] else
                                            "no_game_link" if not link else
                                            "curated_correction" if correction else
                                            "no_wikidata_item" if not title_to_qid.get(link) else
                                            "no_release_claim" if not event else
                                            "earliest_wikidata_release"),
                    "vote_count": "", "vote_count_status": "not_publicly_disclosed"})
    columns = list(nominations[0])
    write_csv("nominations.csv", nominations, columns)
    write_csv("release_events.csv", events, ["game_wikipedia_url", "wikidata_id", "release_date",
                                            "date_precision", "platform_ids", "place_ids",
                                            "statement_id", "source_url"])
    print(f"{len(links)} linked games, {len(events)} release claims; "
          f"{sum(bool(r['original_release_date']) for r in nominations)} nominations dated")


if __name__ == "__main__":
    main()
