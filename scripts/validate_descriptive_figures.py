"""Verify figure coverage and a few analytically important edge cases."""

import json
import subprocess

import polars as pl
from bs4 import BeautifulSoup

from build_descriptive_figures import OUTPUT, ROOT, bins, clean_data


def main():
    rows, categories, _ = clean_data()
    months = list(OUTPUT.glob("f_*/*_month.html"))
    weeks = list(OUTPUT.glob("f_*/*_week.html"))
    assert len(months) == categories.height == 354
    assert len(weeks) == categories.height + 12 == 366
    assert all((OUTPUT / f"f_{year}" / "index.html").exists() for year in range(2014, 2026))
    assert (OUTPUT / "index.html").exists()
    assert (OUTPUT / "assets/plotly.min.js").stat().st_size > 1_000_000
    assert (OUTPUT / ".nojekyll").exists()
    pages = list(OUTPUT.rglob("*.html"))
    assert len(pages) == 734  # 720 figures, 12 year indexes, home and nominees
    for page in pages:
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        for tag, attribute in (("a", "href"), ("script", "src")):
            for element in soup.find_all(tag):
                target = element.get(attribute)
                if target and not target.startswith(("http:", "https:", "#")):
                    assert (page.parent / target).is_file(), f"Broken {attribute} in {page}: {target}"

    table = BeautifulSoup((OUTPUT / "nominees.html").read_text(encoding="utf-8"), "html.parser")
    records = json.loads(table.find("script", id="nominees").string)
    assert len(records) == rows.height == 1774
    assert sum(r["Won"] for r in records) == rows.filter(pl.col("won")).height
    assert any(r["Name"] == "Megabonk" and r["Status"] == "withdrawn" for r in records)
    assert all(set(("Name", "Category", "Year", "Released", "Won")).issubset(r) for r in records)
    scripts = table.find_all("script")
    js = scripts[-1].string
    if subprocess.run(["node", "--check"], input=js, text=True, capture_output=True).returncode:
        raise ValueError("Searchable table JavaScript failed syntax check")

    goty = rows.filter((pl.col("year") == 2014) & (pl.col("category") == "Game of the Year"))
    winner = goty.filter(pl.col("won")).to_dicts()[0]
    assert winner["released_date"].isoformat() == "2014-11-18"
    assert any(r["period"].isoformat() == "2014-11-17" and r["winner_count"] == 1
               for r in bins(goty, "week"))
    bayonetta = goty.filter(pl.col("game_title") == "Bayonetta 2").to_dicts()[0]
    assert bayonetta["released_date"].isoformat() == "2014-09-20"
    for year, title, expected in ((2016, "Block'hood", "2016-03-10"),
                                  (2016, "The King of Fighters XIV", "2016-08-23"),
                                  (2019, "Monster Hunter World: Iceborne", "2019-09-06"),
                                  (2014, "Valiant Hearts: The Great War", "2014-06-25"),
                                  (2018, "Overcooked 2", "2018-08-07"),
                                  (2019, "Beat Saber", "2019-05-21"),
                                  (2025, "Umamusume: Pretty Derby", "2025-06-26"),
                                  (2014, "Ultra Street Fighter IV", "2014-06-03"),
                                  (2014, "Super Smash Bros. for Nintendo 3DS", "2014-09-13"),
                                  (2016, "Rez Infinite", "2016-10-13"),
                                  (2021, "Nier Replicant ver 1.22474487139", "2021-04-22"),
                                  (2021, "Resident Evil 4", "2021-10-21"),
                                  (2023, "Resident Evil Village", "2023-02-22"),
                                  (2024, "Arizona Sunshine Remake", "2024-10-17"),
                                  (2017, "Persona 5", "2017-04-04"),
                                  (2020, "Hades", "2020-09-17")):
        releases = rows.filter((pl.col("year") == year) &
                               (pl.col("game_title") == title))["released_date"].to_list()
        assert releases and all(value.isoformat() == expected for value in releases)
    corrected = pl.read_csv(ROOT / "data/nominations.csv", infer_schema_length=0)
    assert corrected.filter(pl.col("game_title") == "Bayonetta 2")["release_date_status"][0] == "curated_correction"

    annual_2024 = (OUTPUT / "f_2024/all_categories_week.html").read_text(encoding="utf-8")
    assert "Website voting opens: 2024-11-18" in annual_2024
    assert "Website voting closes: 2024-12-11" in annual_2024
    assert '"text":["' in annual_2024  # weekly winner counts rendered above bars
    assert "Nominees: %{y}" in annual_2024
    assert "customdata[2]" not in annual_2024  # hover shows counts, not long nominee lists
    annual_2023 = (OUTPUT / "f_2023/all_categories_week.html").read_text(encoding="utf-8")
    assert "Website voting opens:" not in annual_2023
    assert "reported open by 2023-11-13" in annual_2023
    assert "Website voting closes: 2023-12-06" in annual_2023
    annual_2018 = (OUTPUT / "f_2018/all_categories_week.html").read_text(encoding="utf-8")
    assert "Website voting closes:" not in annual_2018
    assert "2018 Discord vote" in annual_2018
    honorary = (OUTPUT / "f_2014/2014-22_industry-icon-award_week.html").read_text(encoding="utf-8")
    assert "No day-precision game releases to plot" in honorary

    print(f"Validated {len(months)} monthly + {len(weeks)} weekly figures, "
          f"{len(records)} searchable rows, local links and documented vote markers")


if __name__ == "__main__":
    main()
