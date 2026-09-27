"""Check category coverage, arithmetic year means, and a hand-checkable case."""

import statistics
from datetime import date

import polars as pl

from build_descriptive_figures import ROOT


def main():
    category = pl.read_csv(ROOT / "data/category_release_diffs.csv")
    annual = pl.read_csv(ROOT / "data/year_category_release_diffs.csv")
    assert category.height == 354 and annual.height == 12
    assert category["category_id"].n_unique() == 354
    included = category.filter(pl.col("comparison_status") == "included")
    assert included["winner_minus_others_days"].null_count() == 0
    assert category.filter(pl.col("comparison_status") != "included")["winner_minus_others_days"].null_count() == category.height - included.height

    # 2014 GOTY: Dragon Age (Nov 18) versus Bayonetta 2, Dark Souls II,
    # Hearthstone and Shadow of Mordor. No public-vote date enters this gap.
    winner = date(2014, 11, 18).toordinal()
    losers = [date.fromisoformat(day).toordinal() for day in
              ("2014-09-20", "2014-03-11", "2014-03-11", "2014-09-30")]
    expected = round(winner - statistics.mean(losers), 3)
    goty = category.filter(pl.col("category_id") == "2014-01").to_dicts()[0]
    assert goty["winner_minus_others_days"] == expected == 153.0
    fighting = category.filter(pl.col("category_id") == "2014-12").to_dicts()[0]
    assert fighting["other_nominees_dated"] == 4
    assert 0 < fighting["winner_minus_others_days"] < 200  # award-year versions, not 2008 base game
    vr2021 = category.filter((pl.col("award_year") == 2021) &
                             (pl.col("category") == "Best VR / AR Game")).to_dicts()[0]
    assert vr2021["winner_release_date"] == "2021-10-21"  # VR port, not 2005 original

    for row in annual.to_dicts():
        groups = included.filter(pl.col("award_year") == row["award_year"])
        gaps = groups["winner_minus_others_days"].to_list()
        assert row["categories_used"] == len(gaps)
        assert row["mean_winner_minus_others_days"] == round(statistics.mean(gaps), 1)
        assert row["winner_released_later_categories"] == sum(gap > 0 for gap in gaps)
        assert row["winner_released_earlier_categories"] == sum(gap < 0 for gap in gaps)
    print(f"Validated {included.height} within-category comparisons across 12 years")


if __name__ == "__main__":
    main()
