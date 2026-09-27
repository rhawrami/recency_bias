"""Check GOTY/non-GOTY partitions and arithmetic against source category gaps."""

import csv
import statistics

from build_descriptive_figures import ROOT


def read(name):
    with (ROOT / "data" / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main():
    categories = [r for r in read("category_release_diffs.csv")
                  if r["comparison_status"] == "included"]
    yearly = read("goty_vs_non_goty_by_year.csv")
    overall = {r["comparison_group"]: r for r in read("goty_vs_non_goty_overall.csv")}
    assert len(categories) == 269 and len(yearly) == 12
    assert int(overall["goty"]["categories_used"]) == 12
    assert int(overall["all_non_goty"]["categories_used"]) == 257
    assert sum(int(overall[group]["categories_used"]) for group in
               ("standard_non_goty", "ongoing_community", "esports_game", "players_voice")) == 257
    assert int(overall["players_voice"]["categories_used"]) == 7

    for row in yearly:
        year = row["award_year"]
        other = [float(r["winner_minus_others_days"]) for r in categories
                 if r["award_year"] == year and r["category"] != "Game of the Year"]
        assert len(other) == int(row["non_goty_categories"])
        assert round(statistics.mean(other), 1) == float(row["non_goty_mean_gap_days"])
        assert round(statistics.median(other), 1) == float(row["non_goty_median_gap_days"])
        assert sum(value > 0 for value in other) == int(row["non_goty_winner_later_count"])
    print("Validated 12 GOTY and 257 non-GOTY category comparisons across 12 years")


if __name__ == "__main__":
    main()
