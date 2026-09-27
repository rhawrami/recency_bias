"""Annual metadata plus the separately sourced voting-clock ledger."""

from build_awards import write_csv
from build_voting_timeline import FIELDS, timeline


# Ceremony date, nominee announcement and eligibility cutoff. Voting dates
# are sourced separately in voting_timeline.csv; do not infer from these.
DATES = {
    2014: ("2014-12-05", "2014-11-20", "2014-11-25"),
    2015: ("2015-12-03", "2015-11-13", "2015-11-24"),
    2016: ("2016-12-01", "2016-11-16", "2016-11-24"),
    2017: ("2017-12-07", "2017-11-14", "2017-11-27"),
    2018: ("2018-12-06", "2018-11-13", "2018-11-16"),
    2019: ("2019-12-12", "2019-11-19", "2019-11-15"),
    2020: ("2020-12-10", "2020-11-18", "2020-11-20"),
    2021: ("2021-12-09", "2021-11-16", "2021-11-19"),
    2022: ("2022-12-08", "2022-11-14", "2022-11-18"),
    2023: ("2023-12-07", "2023-11-13", "2023-11-17"),
    2024: ("2024-12-12", "2024-11-18", "2024-11-22"),
    2025: ("2025-12-11", "2025-11-17", "2025-11-21"),
}

NOTES = {
    2014: "Separate jury-voted, fan-voted and honorary categories; cutoff after nominee announcement.",
    2015: "Commercial-release cutoff after nominee announcement.",
    2016: "Two fan creations were removed from the published nominations after announcement.",
    2017: "Commercial OR early-access release accepted; Best Ongoing introduced; fan-choice categories public-only.",
    2018: "Official-site votes shared on social media received extra weighting within the fan-vote calculation.",
    2019: "Eligibility cutoff precedes nominee announcement; Player's Voice used multiple public rounds.",
    2020: "Nomination ballots due Nov 6 but updates accepted through Nov 13; Most Anticipated and Player's Voice public-only.",
    2021: "Specialized juries for accessibility and esports; Players' Voice public-only.",
    2022: "Specialized juries for accessibility, adaptation, esports; Players' Voice public-only.",
    2023: "Players' Voice opened separately from ordinary public voting; older ongoing games and expansions nominated.",
    2024: "DLC, expansions, remakes, remasters and seasonal content eligible; Game Changer honorary category added.",
    2025: "DLC, expansions, remakes, remasters and seasonal content eligible; withdrawn Debut Indie nomination needs audit.",
}


def main():
    clocks = timeline()
    write_csv("voting_timeline.csv", clocks, FIELDS)

    def entry(year, clock, round=""):
        # Flat ceremony columns always use the main awards website, not a
        # Discord window which might differ. The ledger retains both.
        return next((r for r in clocks if r["year"] == year and r["clock"] == clock
                     and r["round"] == round and r["channel"] == "awards website"), {})

    rows = []
    for year, dates in DATES.items():
        ceremony, announcement, cutoff = dates
        public = entry(year, "public_winners")
        voice = entry(year, "players_voice", "all")
        jury_nominations = next(r for r in clocks if r["year"] == year and
                                r["clock"] == "jury_nominations")
        jury_winners = next(r for r in clocks if r["year"] == year and
                            r["clock"] == "jury_winners")
        rows.append({
            "year": year, "ceremony_date": ceremony,
            "nominees_announced": announcement,
            "eligibility_cutoff": cutoff,
            "jury_nomination_ballot_sent": jury_nominations["open_date"],
            "jury_nomination_ballot_deadline": "2020-11-06" if year == 2020 else jury_nominations["close_date"],
            "jury_nomination_last_update": jury_nominations["close_date"] if year == 2020 else "",
            "jury_winner_ballot_sent": jury_winners["open_date"],
            "public_vote_open": public.get("open_date", ""),
            "public_vote_first_observed_open": public.get("first_observed_open_date", ""),
            "public_vote_open_confidence": public.get("open_confidence", "unknown"),
            "public_vote_close": public.get("close_date", ""),
            "public_vote_close_time": public.get("close_time", ""),
            "public_vote_close_time_zone": public.get("close_time_zone", ""),
            "public_vote_close_confidence": public.get("close_confidence", "unknown"),
            "players_voice_open": voice.get("open_date", ""),
            "players_voice_close": voice.get("close_date", ""),
            "players_voice_round_2_open": entry(year, "players_voice", "2").get("open_date", ""),
            "players_voice_round_3_open": entry(year, "players_voice", "3").get("open_date", ""),
            "jury_winner_weight": "0.90" if year >= 2017 else "",
            "public_winner_weight": "0.10" if year >= 2017 else "",
            "per_nominee_vote_counts": "not_publicly_disclosed",
            "rules_notes": NOTES[year],
            "date_rules_source_url": f"https://en.wikipedia.org/wiki/The_Game_Awards_{year}",
            "official_winners_url": (f"https://thegameawards.com/rewind/year-{year}"
                                     if year < 2025 else "https://thegameawards.com/nominees/game-of-the-year"),
        })
    write_csv("ceremonies.csv", rows, list(rows[0]))


if __name__ == "__main__":
    main()
