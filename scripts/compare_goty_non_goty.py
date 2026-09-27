"""Compare category-matched release gaps for GOTY and other game awards.

These are descriptive comparisons of the category-release-diff metric, not
independent votes or a causal test of why any voter chose a title.
"""

import statistics

import polars as pl

from build_descriptive_figures import ROOT


def classify(categories):
    name = pl.col("category")
    return categories.with_columns(
        pl.when(name == "Game of the Year").then(pl.lit("goty"))
        .when(name.str.contains("(?i)ongoing|community support"))
          .then(pl.lit("ongoing_community"))
        .when(name.str.contains("(?i)esports game"))
          .then(pl.lit("esports_game"))
        .when(name.str.contains("(?i)player(?:['’]s|s['’]) voice"))
          .then(pl.lit("players_voice"))
        .otherwise(pl.lit("standard_non_goty"))
        .alias("comparison_group")
    )


def summarize(frame, label):
    gaps = frame["winner_minus_others_days"].to_list()
    return {"comparison_group": label, "categories_used": len(gaps),
            "mean_gap_days": round(statistics.mean(gaps), 1) if gaps else None,
            "median_gap_days": round(statistics.median(gaps), 1) if gaps else None,
            "winner_later_count": sum(gap > 0 for gap in gaps),
            "winner_earlier_count": sum(gap < 0 for gap in gaps),
            "tied_count": sum(gap == 0 for gap in gaps)}


def calculate():
    category = pl.read_csv(ROOT / "data/category_release_diffs.csv")
    usable = classify(category.filter(pl.col("comparison_status") == "included"))
    all_non_goty = usable.filter(pl.col("comparison_group") != "goty")
    standard = usable.filter(pl.col("comparison_group") == "standard_non_goty")
    groups = [usable.filter(pl.col("comparison_group") == "goty"), all_non_goty,
              standard]
    labels = ["goty", "all_non_goty", "standard_non_goty"]
    for label in ("ongoing_community", "esports_game", "players_voice"):
        groups.append(usable.filter(pl.col("comparison_group") == label))
        labels.append(label)
    overall = pl.DataFrame([summarize(group, label) for group, label in zip(groups, labels)])

    annual = []
    for year in sorted(usable["award_year"].unique().to_list()):
        yearly = usable.filter(pl.col("award_year") == year)
        goty = yearly.filter(pl.col("comparison_group") == "goty")
        assert goty.height == 1, f"Expected one GOTY comparison for {year}"
        winner_gap = goty["winner_minus_others_days"].item()
        other = yearly.filter(pl.col("comparison_group") != "goty")
        all_summary = summarize(other, "all_non_goty")
        standard_summary = summarize(yearly.filter(pl.col("comparison_group") == "standard_non_goty"),
                                     "standard_non_goty")
        annual.append({"award_year": year, "goty_gap_days": winner_gap,
                       "non_goty_categories": all_summary["categories_used"],
                       "non_goty_mean_gap_days": all_summary["mean_gap_days"],
                       "non_goty_median_gap_days": all_summary["median_gap_days"],
                       "non_goty_winner_later_count": all_summary["winner_later_count"],
                       "non_goty_winner_earlier_count": all_summary["winner_earlier_count"],
                       "non_goty_minus_goty_mean_days": round(
                           statistics.mean(other["winner_minus_others_days"].to_list()) - winner_gap, 1),
                       "standard_non_goty_categories": standard_summary["categories_used"],
                       "standard_non_goty_mean_gap_days": standard_summary["mean_gap_days"],
                       "standard_non_goty_median_gap_days": standard_summary["median_gap_days"]})
    return pl.DataFrame(annual), overall


def main():
    annual, overall = calculate()
    annual.write_csv(ROOT / "data/goty_vs_non_goty_by_year.csv")
    overall.write_csv(ROOT / "data/goty_vs_non_goty_overall.csv")
    print(annual.select("award_year", "goty_gap_days", "non_goty_categories",
                        "non_goty_mean_gap_days", "standard_non_goty_mean_gap_days"))
    print(overall)


if __name__ == "__main__":
    main()
