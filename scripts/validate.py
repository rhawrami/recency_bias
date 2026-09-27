"""Check row integrity and print official-versus-secondary winner differences."""

import collections
import csv
import datetime as dt
import difflib
import re
import unicodedata

from build_awards import DATA


def load(name):
    with (DATA / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def norm(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    roman = {"VIII": "8", "VII": "7", "VI": "6", "IV": "4", "III": "3",
             "II": "2", "IX": "9", "V": "5", "X": "10"}
    text = re.sub(r"\b(?:VIII|VII|VI|IV|III|II|IX|V|X)\b",
                  lambda m: roman[m.group()], text)
    text = text.lower()
    return re.sub(r"[^a-z0-9]", "", text)


def category_key(text):
    text = re.split(r"- presented by ", text, maxsplit=1, flags=re.I)[0]
    key = norm(text)
    for old, new in (("rpg", "roleplayinggame"), ("esportsgameoftheyear", "esportsgame"),
                     ("esportsplayeroftheyear", "esportsplayer"),
                     ("esportsathlete", "esportsplayer"),
                     ("esportsteamoftheyear", "esportsteam"),
                     ("beststudentgame", "studentgameaward")):
        key = key.replace(old, new)
    return key


def main():
    categories = load("categories.csv")
    rows = load("nominations.csv")
    ceremonies = load("ceremonies.csv")
    official = load("official_winners.csv")
    official_2025 = load("official_nominees_2025.csv")
    voting = load("voting_timeline.csv")
    assert {int(x["year"]) for x in ceremonies} == set(range(2014, 2026))
    assert len({x["category_id"] for x in categories}) == len(categories)
    assert len({x["nomination_id"] for x in rows}) == len(rows)
    grouped = collections.defaultdict(list)
    for row in rows:
        grouped[row["category_id"]].append(row)
    for category in categories:
        group = grouped[category["category_id"]]
        assert group, category
        assert sum(x["is_winner"] == "1" for x in group) == (len(group) if category["category_type"] == "honorary" else 1), category
        assert len({(x["nominee_order"], x["nominee"]) for x in group}) == len(group)
    assert all(x["release_date_status"] for x in rows)
    print(f"{len(ceremonies)} ceremonies, {len(categories)} categories, "
          f"{len(rows)} nominations, {len(official)} independently listed official winners")
    print("Release status:", dict(collections.Counter(x["release_date_status"] for x in rows)))
    potential = []
    for result in official:
        candidates = [cat for cat in categories if cat["year"] == result["year"]]
        category = max(candidates, key=lambda x: difflib.SequenceMatcher(None, category_key(x["category"]),
                                                                           category_key(result["category"])).ratio())
        same_category = difflib.SequenceMatcher(None, category_key(category["category"]),
                                                  category_key(result["category"])).ratio()
        winners = [r for r in grouped[category["category_id"]] if r["is_winner"] == "1"]
        matched = any(norm(r["nominee"]) in norm(result["winner"]) or
                      norm(result["winner"]) in norm(r["nominee"]) or
                      norm(r["game_title"]) == norm(result["winner"]) or
                      norm(result["winner"]) in norm(r["raw_nomination"])
                      for r in winners if r["nominee"])
        if not matched or same_category < .60:
            potential.append((result["year"], result["category"], result["winner"],
                              category["category"], "; ".join(r["nominee"] for r in winners)))
    print(f"Official winners needing name/category review: {len(potential)}")
    for item in potential:
        print(" | ".join(item))
    print(f"Official 2025 nominees including Players' Voice finalists: {len(official_2025)}; "
          "withdrawn Megabonk is intentionally absent from that source")
    assert len(official_2025) == 155
    assert sum(r["year"] == "2025" and r["category_type"] != "honorary" and
               r["nomination_status"] == "active" for r in rows) == len(official_2025)
    assert next(r["nominee"] for r in rows if r["year"] == "2023" and
                r["category"] == "Players' Voice" and r["is_winner"] == "1") == "Baldur's Gate 3"
    by_year = {r["year"]: r for r in ceremonies}
    for vote in voting:
        ceremony = by_year[vote["year"]]
        for endpoint, confidence in (("open_date", "open_confidence"),
                                     ("close_date", "close_confidence")):
            if vote[endpoint]:
                dt.date.fromisoformat(vote[endpoint])
                assert vote[confidence].startswith("documented"), vote
                prefix = "open" if endpoint == "open_date" else "close"
                assert vote[prefix + "_source_url"] and vote[prefix + "_source_quote"], vote
                assert vote[endpoint] <= ceremony["ceremony_date"], vote
        if vote["first_observed_open_date"]:
            dt.date.fromisoformat(vote["first_observed_open_date"])
            assert vote["open_confidence"] == "observed_by" and not vote["open_date"], vote
            assert vote["open_source_url"] and vote["open_source_quote"], vote
        assert not (vote["open_date"] and vote["close_date"] and
                    vote["open_date"] > vote["close_date"]), vote
        assert not vote["close_time"] or vote["close_time_zone"], vote
    for ceremony in ceremonies:
        public = next((v for v in voting if v["year"] == ceremony["year"] and
                       v["clock"] == "public_winners" and v["channel"] == "awards website"), None)
        if public:
            assert (ceremony["public_vote_open"] == public["open_date"] and
                    ceremony["public_vote_first_observed_open"] == public["first_observed_open_date"] and
                    ceremony["public_vote_close"] == public["close_date"]), ceremony
    website = [v for v in voting if v["clock"] == "public_winners" and v["channel"] == "awards website"]
    complete = [v["year"] for v in website if v["open_date"] and v["close_date"]]
    assert complete == ["2017", "2024"]
    assert next(v for v in voting if v["year"] == "2018" and v["channel"] == "Discord")["close_date"] == "2018-12-05"
    assert by_year["2018"]["public_vote_close"] == ""
    assert (by_year["2020"]["jury_nomination_ballot_deadline"],
            by_year["2020"]["jury_nomination_last_update"]) == ("2020-11-06", "2020-11-13")
    assert by_year["2024"]["jury_nomination_ballot_deadline"] < by_year["2024"]["eligibility_cutoff"]
    assert (by_year["2025"]["players_voice_open"],
            by_year["2025"]["players_voice_round_2_open"],
            by_year["2025"]["players_voice_round_3_open"]) == (
                "2025-12-01", "2025-12-04", "2025-12-08")
    print(f"Standard website voting: documented full date windows {complete}; "
          f"first observed open by {sum(bool(v['first_observed_open_date']) for v in website)} other years")


if __name__ == "__main__":
    main()
