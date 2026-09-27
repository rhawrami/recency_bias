"""Extract the twelve Game of the Year winner-versus-other-nominee gaps."""

import statistics

import polars as pl

from build_descriptive_figures import ROOT, clean_data
from calculate_category_release_diffs import calculate


def main():
    nominations, _, _ = clean_data()
    comparisons, _ = calculate()
    goty = comparisons.filter(pl.col("category") == "Game of the Year").sort("award_year")
    assert goty.height == 12 and all(s == "included" for s in goty["comparison_status"])
    results = []
    for row in goty.to_dicts():
        nominees = nominations.filter(
            (pl.col("year") == row["award_year"]) &
            (pl.col("category_id") == row["category_id"]) &
            (pl.col("nomination_status") == "active") &
            pl.col("released_date").is_not_null()
        )
        winner_day = nominees.filter(pl.col("won"))["released_date"].item()
        rank = nominees.filter(pl.col("released_date") < winner_day).height + 1
        assert nominees.filter((pl.col("released_date") == winner_day) &
                              ~pl.col("won")).is_empty(), "A tied date requires explicit rank handling"
        results.append({
            "award_year": row["award_year"], "winner": row["winner_name"],
            "winner_release_date": row["winner_release_date"],
            "other_nominees_dated": row["other_nominees_dated"],
            "winner_release_rank_oldest_to_newest": f"{rank}/{nominees.height}",
            "winner_minus_others_days": row["winner_minus_others_days"],
        })
    data = pl.DataFrame(results)
    data.write_csv(ROOT / "data/goty_release_diffs.csv")
    differences = data["winner_minus_others_days"].to_list()
    print(data)
    print(f"Mean: {statistics.mean(differences):.1f} days; median: {statistics.median(differences):.1f} days; "
          f"winner later in {sum(x > 0 for x in differences)}/12 years")


if __name__ == "__main__":
    main()
