"""Mean days from game release to the public-voting date or stated proxy.

An observed-open-by date is a proxy, not an established opening date. For
2014–16, when no voting-day evidence was found, nominee-announcement dates are
explicitly LOW-CONFIDENCE assumptions so the requested table has every year.
Each active nomination counts once per category; games may repeat in a year.
"""

from datetime import date

import polars as pl

from build_descriptive_figures import ROOT, clean_data


def calculate():
    rows, _, ceremonies = clean_data()
    results, coverage = [], []
    for year, ceremony in sorted(ceremonies.items()):
        game_rows = rows.filter((pl.col("year") == year) &
                                (pl.col("nomination_status") == "active") &
                                (pl.col("game_title").is_not_null()) &
                                (pl.col("category_type") != "unreleased_game"))
        dated = game_rows.filter(pl.col("released_date").is_not_null() &
                                 (pl.col("released_date") <= date.fromisoformat(ceremony["ceremony_date"])))
        documented_open = ceremony["public_vote_open"]
        observed_open = ceremony["public_vote_first_observed_open"]
        reference = documented_open or observed_open or ceremony["nominees_announced"]
        basis = ("documented_open" if documented_open else
                 "observed_open_by_proxy" if observed_open else
                 "nominee_announcement_assumption_low_confidence")
        mean_all, mean_winners = None, None
        if reference:
            gaps = dated.with_columns(
                (pl.lit(date.fromisoformat(reference), dtype=pl.Date) - pl.col("released_date"))
                .dt.total_days().alias("days_before_vote_reference")
            )
            mean_all = gaps["days_before_vote_reference"].mean()
            mean_winners = gaps.filter(pl.col("won"))["days_before_vote_reference"].mean()
        results.append({"Award year": year,
                        "avg_diff_all": round(mean_all, 1) if mean_all is not None else None,
                        "avg_diff_winners": round(mean_winners, 1) if mean_winners is not None else None})
        coverage.append({"year": year, "vote_reference": reference,
                         "vote_reference_basis": basis,
                         "active_game_nominations": game_rows.height,
                         "dated_game_nominations": dated.height,
                         "dated_winning_nominations": dated.filter(pl.col("won")).height,
                         "omitted_missing_or_partial_release": game_rows.filter(pl.col("released_date").is_null()).height,
                         "omitted_post_ceremony_release": game_rows.filter(
                             pl.col("released_date").is_not_null() &
                             (pl.col("released_date") > date.fromisoformat(ceremony["ceremony_date"]))
                         ).height})
    return pl.DataFrame(results), pl.DataFrame(coverage)


def main():
    results, coverage = calculate()
    results.write_csv(ROOT / "data/avg_release_lags.csv")
    coverage.write_csv(ROOT / "data/avg_release_lags_coverage.csv")
    print(results)
    print(coverage)


if __name__ == "__main__":
    main()
