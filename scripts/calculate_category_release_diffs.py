"""Compare each winner's release day with other nominees in that category.

Positive winner_minus_others_days means the winner released later (the
direction expected under a winner-stage recency preference). Yearly results
are arithmetic means of available category gaps with equal category weights.
No public-vote opening date is needed: it cancels in this within-category gap.
"""

from datetime import date

import polars as pl

from build_descriptive_figures import ROOT, clean_data


CATEGORY_COLUMNS = [
    "award_year", "category_id", "category", "category_type", "comparison_status",
    "winner_name", "winner_release_date", "other_nominees_dated",
    "other_nominees_missing_date", "winner_minus_others_days",
]


def calculate():
    nominations, categories, ceremonies = clean_data()
    comparisons = []
    for category in categories.to_dicts():
        year = int(category["year"])
        group = nominations.filter(
            (pl.col("category_id") == category["category_id"]) &
            (pl.col("nomination_status") == "active")
        )
        winners = group.filter(pl.col("won"))
        others = group.filter(~pl.col("won"))
        ceremony_date = date.fromisoformat(ceremonies[year]["ceremony_date"])
        dated_others = others.filter(
            pl.col("released_date").is_not_null() &
            (pl.col("released_date") <= ceremony_date)
        )
        result = {"award_year": year, "category_id": category["category_id"],
                  "category": category["category"], "category_type": category["category_type"],
                  "comparison_status": "", "winner_name": "; ".join(winners["nominee"].to_list()),
                  "winner_release_date": None, "other_nominees_dated": dated_others.height,
                  "other_nominees_missing_date": others.height - dated_others.height,
                  "winner_minus_others_days": None}
        kind = category["category_type"]
        if kind == "unreleased_game":
            result["comparison_status"] = "unreleased_game_award"
        elif kind not in ("game", "performance"):
            result["comparison_status"] = "non_game_award"
        elif winners.height != 1:
            result["comparison_status"] = "winner_count_not_one"
        else:
            winner = winners.to_dicts()[0]
            released = winner["released_date"]
            if released is None:
                result["comparison_status"] = "winner_release_missing_or_partial"
            elif released > ceremony_date:
                result["comparison_status"] = "winner_released_after_ceremony"
            else:
                result["winner_release_date"] = released.isoformat()
                if dated_others.is_empty():
                    result["comparison_status"] = "no_dated_other_nominees"
                else:
                    result["comparison_status"] = "included"
                    winner_day = (released - date(1970, 1, 1)).days
                    average_other_day = (dated_others.select(
                        pl.col("released_date").cast(pl.Int32).mean()
                    ).item())
                    result["winner_minus_others_days"] = round(winner_day - average_other_day, 3)
        comparisons.append(result)

    by_category = pl.DataFrame(comparisons).select(CATEGORY_COLUMNS).sort("award_year", "category_id")
    included = by_category.filter(pl.col("comparison_status") == "included")
    by_year = (included.group_by("award_year").agg(
        pl.len().alias("categories_used"),
        pl.col("winner_minus_others_days").mean().round(1).alias("mean_winner_minus_others_days"),
        pl.col("winner_minus_others_days").filter(pl.col("winner_minus_others_days") > 0)
          .count().alias("winner_released_later_categories"),
        pl.col("winner_minus_others_days").filter(pl.col("winner_minus_others_days") < 0)
          .count().alias("winner_released_earlier_categories"),
    ).sort("award_year"))
    return by_category, by_year


def main():
    categories, years = calculate()
    categories.write_csv(ROOT / "data/category_release_diffs.csv")
    years.write_csv(ROOT / "data/year_category_release_diffs.csv")
    print(years)
    print(categories.group_by("comparison_status").len().sort("comparison_status"))


if __name__ == "__main__":
    main()
