"""Curated evidence for three distinct Game Awards voting clocks, 2014–2025.

An 'observed_by' date proves that voting was available *by* that day; it does
not claim to be the instant that voting opened. Only explicit announced start
dates populate open_date. Source wording and provenance accompany every fact.
"""

from build_awards import write_csv


FIELDS = [
    "year", "clock", "round", "channel", "open_date", "open_time",
    "open_time_zone", "first_observed_open_date", "close_date", "close_time",
    "close_time_zone", "open_confidence", "close_confidence",
    "open_source_type", "close_source_type", "open_source_url",
    "close_source_url", "open_source_quote", "close_source_quote", "notes",
]


def record(year, clock, *, round="", channel="", open_date="", open_time="",
           open_time_zone="", first_observed_open_date="", close_date="",
           close_time="", close_time_zone="", open_confidence="unknown",
           close_confidence="unknown", open_source_type="", close_source_type="",
           open_source_url="", close_source_url="", open_source_quote="",
           close_source_quote="", notes=""):
    return dict(locals())


def timeline():
    rows = []
    for year in range(2014, 2026):
        rows.extend([
            record(year, "jury_nominations", channel="editorial jury",
                   notes="Nominee-selection ballots; not the later public winner vote."),
            record(year, "jury_winners", channel="editorial jury",
                   notes="Final jury winner ballots; not the earlier nomination ballots."),
        ])
        if year < 2017:
            rows.append(record(year, "public_fan_choice", channel="various",
                               notes="Fan-selected categories existed, but their voting dates are unverified."))
        else:
            rows.append(record(year, "public_winners", channel="awards website",
                               notes="Standard public contribution to winner selection; do not use Players' Voice dates."))
        if year >= 2019:
            rows.append(record(year, "players_voice", round="all", channel="awards website",
                               notes="Separate fully public multi-round bracket; start/end refer to the entire bracket."))

    def set_row(year, clock, *, round="", channel="", **changes):
        if clock == "players_voice" and not round:
            round = "all"
        row = next(r for r in rows if r["year"] == year and r["clock"] == clock
                   and r["round"] == round and (not channel or r["channel"] == channel))
        row.update(changes)

    wiki2017 = "https://en.wikipedia.org/wiki/The_Game_Awards_2017#Awards"
    for clock in ("public_winners", "public_fan_choice"):
        if clock == "public_fan_choice":
            rows.append(record(2017, clock, channel="various",
                               notes="Fan's choice categories were fully public-voted."))
        set_row(2017, clock, open_date="2017-11-14", close_date="2017-12-06",
                open_confidence="documented_secondary", close_confidence="documented_secondary",
                open_source_type="annual_cited_summary", close_source_type="annual_cited_summary",
                open_source_url=wiki2017, close_source_url=wiki2017,
                open_source_quote="Public voting for awards ran from November 14 until December 6.",
                close_source_quote="Public voting for awards ran from November 14 until December 6.")

    press2018 = "https://www.pcgamer.com/the-game-awards-2018-nominations-have-been-announced/"
    set_row(2018, "public_winners", first_observed_open_date="2018-11-13",
            open_confidence="observed_by", open_source_type="organizer_post_quoted_in_contemporary_report",
            open_source_url=press2018,
            open_source_quote="Here's a look at the top nominees for #TheGameAwards. Vote now at https://t.co/9kiptu92wd",
            notes="Organiser's Nov 13 post says vote now; exact website launch and website close are unverified. Discord has a separately documented window.")
    rows.append(record(2018, "public_winners", channel="Discord", open_date="2018-11-13",
                       close_date="2018-12-05", open_confidence="documented_secondary",
                       close_confidence="documented_secondary", open_source_type="contemporary_report",
                       close_source_type="contemporary_report", open_source_url=press2018,
                       close_source_url=press2018,
                       open_source_quote="Voting on the server will open on November 13 and run until December 5.",
                       close_source_quote="Voting on the server will open on November 13 and run until December 5.",
                       notes="Dates explicitly describe voting on the Discord server, not necessarily the website."))

    press2019 = "https://www.pcgamer.com/death-stranding-and-control-lead-the-game-awards-2019-nominations/"
    set_row(2019, "public_winners", first_observed_open_date="2019-11-19",
            open_confidence="observed_by", open_source_type="contemporary_report",
            open_source_url=press2019,
            open_source_quote="Voting for The Game Awards 2019 is live now.",
            notes="Published Nov 19; exact opening and closing dates remain unverified.")

    press2020 = "https://www.ign.com/articles/the-game-awards-2020-nominees-announced"
    set_row(2020, "public_winners", first_observed_open_date="2020-11-18",
            close_date="2020-12-09", open_confidence="observed_by",
            close_confidence="documented_secondary", open_source_type="contemporary_report",
            close_source_type="annual_cited_summary", open_source_url=press2020,
            close_source_url="https://en.wikipedia.org/wiki/The_Game_Awards_2020#Winners_and_nominees",
            open_source_quote="The nominees in each category are now available for public voting",
            close_source_quote="closed on December 9",
            notes="IGN page was published Nov 18 and modified Dec 3; opening is an observed-by bound, not an exact instant." )
    jury2020 = "https://www.polygon.com/2020/11/18/21574150/the-game-awards-nominations-2020-games-list"
    set_row(2020, "jury_nominations", open_date="2020-10-29", close_date="2020-11-13",
            open_confidence="documented_secondary", close_confidence="documented_secondary",
            open_source_type="jury_outlet_report", close_source_type="jury_outlet_report",
            open_source_url=jury2020, close_source_url=jury2020,
            open_source_quote="Ballots were sent out to outlets on Oct. 29, due back on Nov. 6",
            close_source_quote="Outlets also had until Nov. 13 to send in updated versions of those ballots",
            notes="Initial ballot deadline Nov 6; Nov 13 was the last stated opportunity to update.")

    press2021 = "https://www.vg247.com/the-game-awards-2021-nominees"
    set_row(2021, "public_winners", first_observed_open_date="2021-11-16",
            close_date="2021-12-08", open_confidence="observed_by",
            close_confidence="documented_secondary", open_source_type="contemporary_report",
            close_source_type="annual_cited_summary", open_source_url=press2021,
            close_source_url="https://en.wikipedia.org/wiki/The_Game_Awards_2021#Winners_and_nominees",
            open_source_quote="With the announcement of nominees, you can now vote",
            close_source_quote="until December 8")

    press2022 = "https://www.ign.com/articles/the-game-awards-2022-nominations-elden-ring-god-of-war-ragnarok"
    set_row(2022, "public_winners", first_observed_open_date="2022-11-14",
            close_date="2022-12-07", open_confidence="observed_by",
            close_confidence="documented_secondary", open_source_type="contemporary_report",
            close_source_type="annual_cited_summary", open_source_url=press2022,
            close_source_url="https://en.wikipedia.org/wiki/The_Game_Awards_2022#Winners_and_nominees",
            open_source_quote="The public can now vote for the nominees they think are most deserving of each individual award",
            close_source_quote="until December 7",
            notes="IGN page was published Nov 14 and later modified Dec 5; opening is observed-by.")
    wiki2022 = "https://en.wikipedia.org/wiki/The_Game_Awards_2022#Winners_and_nominees"
    set_row(2022, "players_voice", open_date="2022-11-28", close_date="2022-12-07",
            open_confidence="documented_secondary", close_confidence="documented_secondary",
            open_source_type="annual_cited_summary", close_source_type="annual_cited_summary",
            open_source_url=wiki2022, close_source_url=wiki2022,
            open_source_quote="three rounds of voting, which ran from November 28 to December 7",
            close_source_quote="three rounds of voting, which ran from November 28 to December 7")

    press2023 = "https://www.pcgamer.com/baldurs-gate-3-and-alan-wake-2-lead-the-game-awards-with-8-nominations-each/"
    set_row(2023, "public_winners", first_observed_open_date="2023-11-13",
            close_date="2023-12-06", close_time="18:00", close_time_zone="America/Los_Angeles",
            open_confidence="observed_by", close_confidence="documented_secondary",
            open_source_type="contemporary_report", close_source_type="contemporary_report",
            open_source_url=press2023, close_source_url=press2023,
            open_source_quote="Voting is now open to the public on The Game Awards website",
            close_source_quote="until Wednesday, December 6 at 6 pm Pacific")
    wiki2023 = "https://en.wikipedia.org/wiki/The_Game_Awards_2023#Winners_and_nominees"
    set_row(2023, "players_voice", open_date="2023-11-27",
            open_confidence="documented_secondary", open_source_type="annual_cited_summary",
            open_source_url=wiki2023, open_source_quote="voting opened on November 27")

    press2024 = "https://www.animenewsnetwork.com/press-release/2024-11-14/the-game-awards-2024-nominees-to-be-announced-nov-18-at-9am-pt/.217874"
    report2024 = "https://deadline.com/2024/11/the-game-award-nominations-2024-1236180078/"
    for channel in ("awards website", "Discord"):
        if channel == "Discord":
            rows.append(record(2024, "public_winners", channel=channel,
                               first_observed_open_date="2024-11-18", close_date="2024-12-11",
                               open_confidence="observed_by", close_confidence="documented_secondary",
                               open_source_type="contemporary_report", close_source_type="contemporary_report",
                               open_source_url=report2024, close_source_url=report2024,
                               open_source_quote="Fans can participate in voting from now through December 11 via The Game Awards’ website and Discord server.",
                               close_source_quote="Fans can participate in voting from now through December 11 via The Game Awards’ website and Discord server.",
                               notes="Deadline published Nov 18; Discord-specific opening hour and closing hour not reported."))
            continue
        set_row(2024, "public_winners", open_date="2024-11-18",
                close_date="2024-12-11", close_time="18:00",
                close_time_zone="America/Los_Angeles", open_confidence="documented_primary",
                close_confidence="documented_primary", open_source_type="organizer_press_release",
                close_source_type="organizer_press_release", open_source_url=press2024,
                close_source_url=press2024,
                open_source_quote="via authenticated online voting on www.thegameawards.com from November 18th to December 11th at 6 pm PT",
                close_source_quote="via authenticated online voting on www.thegameawards.com from November 18th to December 11th at 6 pm PT",
                notes="Nominee announcement was scheduled for Nov 18 at 9am PT; the release does not specify the voting site's opening hour.")
    jury2024 = "https://kotaku.com/game-awards-snub-dragon-age-veilguard-eligibility-dates-1851704052"
    set_row(2024, "jury_nominations", close_date="2024-11-12",
            close_confidence="documented_secondary", close_source_type="jury_outlet_interviews",
            close_source_url=jury2024,
            close_source_quote="According to staffers at jury outlets Kotaku has spoken to, ballots were due on November 12.",
            notes="Outlet-level internal deadlines could precede Nov 12; jury ballot opening unknown.")
    wiki2024 = "https://en.wikipedia.org/wiki/The_Game_Awards_2024#Winners_and_nominees"
    set_row(2024, "players_voice", open_date="2024-12-02",
            open_confidence="documented_secondary", open_source_type="annual_cited_summary",
            open_source_url=wiki2024, open_source_quote="voting opened on December 2")

    press2025 = "https://variety.com/2025/gaming/news/game-awards-nominations-2025-list-1236583686/"
    voting2025 = "https://www.videogameschronicle.com/news/clair-obscur-and-playstation-leads-the-game-awards-2025-nominations/"
    set_row(2025, "public_winners", first_observed_open_date="2025-11-17",
            close_date="2025-12-10", close_time="18:00",
            close_time_zone="America/Los_Angeles", open_confidence="observed_by",
            close_confidence="documented_secondary", open_source_type="contemporary_report",
            close_source_type="contemporary_report", open_source_url=voting2025,
            close_source_url=voting2025,
            open_source_quote="From today until December 10 at 6 pm PT, fans can vote for their winners in all categories",
            close_source_quote="From today until December 10 at 6 pm PT, fans can vote for their winners in all categories",
            notes="VGC reported this on Nov 17; 'from today' confirms the day voting was available, not its launch hour.")
    set_row(2025, "jury_winners", open_date="2025-11-18",
            open_confidence="documented_secondary", open_source_type="jury_ballot_report",
            open_source_url=press2025,
            open_source_quote="In a statement sent to its jury members Tuesday, along with the final voting ballot",
            notes="Article published Mon Nov 17, updated after Tuesday's Megabonk withdrawal; jury final ballot was sent Nov 18, close unreported.")
    official2025 = "https://thegameawards.com/brackets/players-voice"
    set_row(2025, "players_voice", open_date="2025-12-01",
            open_confidence="documented_primary", open_source_type="organizer_bracket",
            open_source_url=official2025, open_source_quote="Round 1 Opens Dec 1",
            notes="Three-round bracket. No final closing hour stated on this page.")
    for round, date, quote in (("2", "2025-12-04", "Round 2 Opens Dec 4"),
                               ("3", "2025-12-08", "Round 3 Opens Dec 8")):
        rows.append(record(2025, "players_voice", round=round, channel="awards website",
                           open_date=date, open_confidence="documented_primary",
                           open_source_type="organizer_bracket", open_source_url=official2025,
                           open_source_quote=quote,
                           notes="Round start only; round closing timestamp not published on the page."))
    order = {"jury_nominations": 0, "jury_winners": 1, "public_winners": 2,
             "public_fan_choice": 3, "players_voice": 4}
    return sorted(rows, key=lambda row: (row["year"], order[row["clock"]],
                                         0 if row["channel"] == "awards website" else 1,
                                         0 if row["round"] in ("", "all") else int(row["round"])))


def main():
    write_csv("voting_timeline.csv", timeline(), FIELDS)


if __name__ == "__main__":
    main()
