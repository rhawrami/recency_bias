"""Make offline Plotly figures and a searchable table from the awards dataset.

Run after building nominations and ceremonies. Figures use one nominee-category
record per observation; source release dates with less than day precision never
get assigned an arbitrary month or week.
"""

import html
import json
import re
from datetime import date, timedelta
from pathlib import Path

import polars as pl
import plotly.graph_objects as go
from plotly.offline.offline import get_plotlyjs


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs"
BG = "#282A36"
TEXT = "#F8F8F2"
PINK = "#FFC2E2"
BLUE = "#AED9FF"
GREEN = "#B8E8D0"
PURPLE = "#CFBDFF"
YELLOW = "#FFE7A6"
FONT = "Palatino, 'Palatino Linotype', 'Book Antiqua', serif"
DAY_MS = 86_400_000

CSS = f"""
html, body {{ background: {BG}; color: {TEXT}; font-family: {FONT}; margin: 0; }}
main {{ margin: auto; max-width: 1250px; padding: 24px 28px 70px; }}
a {{ color: {BLUE}; }} a:hover, a:focus-visible {{ color: {PINK}; }}
h1, h2 {{ color: {TEXT}; }}
.note {{ border-left: 4px solid {PURPLE}; background: #383a49; padding: 12px 18px;
         margin: 4px 0 18px; line-height: 1.55; }}
.note li {{ margin: 5px 0; }}
.card {{ background: #383a49; border-radius: 12px; margin: 12px 0; padding: 14px 18px; }}
.muted {{ color: {YELLOW}; }}
"""


def clean_data():
    rows = pl.read_csv(ROOT / "data/nominations.csv", infer_schema_length=0)
    rows = rows.with_columns(
        pl.col("year").cast(pl.Int32),
        (pl.col("is_winner") == "1").alias("won"),
        pl.when(pl.col("award_year_release_date").is_not_null())
          .then(pl.col("award_year_release_date"))
          .when(pl.col("original_release_precision") == "day")
          .then(pl.col("original_release_date"))
          .otherwise(None)
          .str.strptime(pl.Date, "%Y-%m-%d", strict=False)
          .alias("released_date"),
    )
    categories = pl.read_csv(ROOT / "data/categories.csv", infer_schema_length=0)
    ceremonies = pl.read_csv(ROOT / "data/ceremonies.csv", infer_schema_length=0)
    return rows, categories, {int(row["year"]): row for row in ceremonies.to_dicts()}


def bins(rows, period):
    frequency = "1mo" if period == "month" else "1w"
    return (rows.filter(pl.col("released_date").is_not_null())
            .with_columns(pl.col("released_date").dt.truncate(frequency).alias("period"))
            .group_by("period")
            .agg(pl.len().alias("nominee_count"),
                 pl.col("won").cast(pl.Int32).sum().alias("winner_count"))
            .sort("period").to_dicts())


def month_end(start):
    return date(start.year + (start.month == 12), start.month % 12 + 1, 1)


def notes(rows, ceremony, *, annual=False):
    active = rows.filter(pl.col("nomination_status") == "active")
    missing = active.filter(pl.col("released_date").is_null()).height
    winners_missing = active.filter(pl.col("won") & pl.col("released_date").is_null()).height
    result = ["One observation is one nomination in one category; a game nominated in several categories is counted several times.",
              "Use the sourced award-year release where available; otherwise use the earliest day-precision public release. Older launches, early access, ports and ongoing-game updates may require different dates for causal comparisons."]
    if missing:
        result.append(f"{missing} of {active.height} active nomination(s) lack a usable day-precision game release and are absent from the bars.")
    if winners_missing:
        result.append(f"{winners_missing} winning nomination(s) have no plottable release date, so their bar cannot be highlighted or annotated.")
    if rows.filter(pl.col("nomination_status") == "withdrawn").height:
        result.append("Withdrawn nominations are retained in the searchable table but excluded from these histograms.")
    previous = active.filter(pl.col("released_date").is_not_null() &
                             (pl.col("released_date").dt.year() < int(ceremony["year"]))).height
    if previous:
        result.append(f"{previous} active nomination(s) use releases before the award year; calendar-year labels are retained rather than folding those dates into this year's months or weeks.")
    if annual:
        result.append("This annual overview excludes Most Anticipated games and releases after the ceremony; counts are nominations and winning nominations, not distinct games.")
    elif rows.filter(pl.col("category_type") == "unreleased_game").height:
        result.append("Most Anticipated recognizes unreleased titles. Dates here may be later actual launches and are not eligibility dates for this award.")
    if ceremony["public_vote_open"]:
        result.append("The voting-opening line uses a documented website start day; the exact opening hour is not recorded.")
    elif ceremony["public_vote_first_observed_open"]:
        result.append(f"Website voting was reported open by {ceremony['public_vote_first_observed_open']}; this is a bound, not a verified opening date, so no opening line is drawn.")
    else:
        result.append("The website voting-opening date has not been verified; no opening line is drawn.")
    if not ceremony["public_vote_close"]:
        result.append("The website voting closing date is unverified; no closing line is drawn.")
    if ceremony["year"] == "2018":
        result.append("A separate 2018 Discord vote ran November 13–December 5; its dates are not applied to the website's voting markers.")
    return result


def plot(rows, ceremony, period, title, output_path, *, annual=False):
    counts = bins(rows.filter(pl.col("nomination_status") == "active"), period)
    fig = go.Figure()
    if counts:
        midpoints, widths = [], []
        for item in counts:
            start = item["period"]
            end = month_end(start) if period == "month" else start + timedelta(days=7)
            days = (end - start).days
            midpoints.append(start + timedelta(days=days / 2))
            widths.append(days * DAY_MS * 0.84)
        colors = [PINK if item["winner_count"] else (BLUE, GREEN, PURPLE, YELLOW)[index % 4]
                  for index, item in enumerate(counts)]
        fig.add_bar(
            x=midpoints, y=[r["nominee_count"] for r in counts], width=widths,
            marker_color=colors, marker_line_color=BG, marker_line_width=1,
            opacity=0.83, name="Nominees (pink = winner week/month)",
            customdata=[[r["winner_count"], r["period"].isoformat()] for r in counts],
            hovertemplate=("<b>%{customdata[1]}</b><br>Nominees: %{y}"
                           "<br>Winning nominations: %{customdata[0]}<extra></extra>"),
            text=[str(r["winner_count"]) for r in counts] if annual else None,
            textposition="outside" if annual else None,
            textfont={"color": TEXT, "family": FONT, "size": 11},
            cliponaxis=False,
        )
    else:
        fig.add_annotation(text="No day-precision game releases to plot for this category.",
                           x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                           font={"family": FONT, "color": YELLOW, "size": 20})

    high = max((item["nominee_count"] for item in counts), default=1)
    for field, label, color in (("public_vote_open", "Website voting opens", PURPLE),
                                ("public_vote_close", "Website voting closes", YELLOW)):
        value = ceremony[field]
        if value:
            fig.add_scatter(x=[value, value], y=[0, high * (1.21 if annual else 1.13)],
                            mode="lines", name=f"{label}: {value}",
                            line={"color": color, "dash": "dot", "width": 2.5},
                            hovertemplate=f"{label}: {value}<extra></extra>")
    fig.update_layout(
        title={"text": title, "font": {"family": FONT, "color": TEXT, "size": 22}},
        font={"family": FONT, "color": TEXT, "size": 14},
        paper_bgcolor=BG, plot_bgcolor=BG, height=580,
        margin={"l": 68, "r": 28, "t": 106, "b": 85},
        legend={"orientation": "h", "y": 1.14, "x": 0, "font": {"size": 12}},
        bargap=0.16,
        xaxis={"title": "Release month (calendar date)" if period == "month" else "Week beginning Monday (calendar date)",
               "tickformat": "%b %Y" if period == "month" else "%d %b %Y",
               "gridcolor": "#44475A", "linecolor": TEXT, "zeroline": False,
               "rangeslider": {"visible": bool(counts and
                   (counts[-1]["period"] - counts[0]["period"]).days > 730)}},
        yaxis={"title": "Nomination count", "rangemode": "tozero",
               "range": [0, high * (1.39 if annual else 1.23)], "gridcolor": "#44475A",
               "dtick": 1 if high <= 12 else None, "zeroline": False},
    )
    caveats = notes(rows, ceremony, annual=annual)
    figure = fig.to_html(full_html=False, include_plotlyjs="../assets/plotly.min.js",
                         config={"responsive": True, "displaylogo": False})
    note_list = "".join(f"<li>{html.escape(message)}</li>" for message in caveats)
    output_path.write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title>"
        f"<style>{CSS}</style></head><body><main><nav><a href='index.html'>Year index</a> · "
        "<a href='../index.html'>All years</a> · <a href='../nominees.html'>Search nominees</a></nav>"
        f"{figure}<section class='note'><strong>Figure notes</strong><ul>{note_list}</ul></section>"
        "</main></body></html>", encoding="utf-8")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-") or "category"


def write_table(rows):
    data = [{"Name": row["nominee"], "Category": row["category"], "Year": row["year"],
             "Released": (row["released_date"].isoformat() if row["released_date"] else
                          row["original_release_date"] or ""),
             "Won": bool(row["won"]), "Status": row["nomination_status"],
             "ReleaseBasis": (row["award_year_release_basis"] if row["award_year_release_date"]
                              else "earliest documented public release" if row["released_date"] else
                              "partial date only" if row["original_release_date"] else "unavailable")}
            for row in rows.to_dicts()]
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    years = "".join(f"<option value='{y}'>{y}</option>" for y in sorted({r["Year"] for r in data}))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Game Awards nominees</title>
<style>{CSS}
label {{ margin-right: 12px; }} input, select {{ padding: 9px; border: 1px solid {PURPLE};
 background: {BG}; color: {TEXT}; border-radius: 5px; font: 17px {FONT}; }}
input {{ width: min(420px, 85vw); }} .filters {{ display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }}
.scroll {{ max-height: 74vh; overflow: auto; margin-top: 15px; border: 1px solid #44475A; }}
table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 8px 12px; text-align: left;
 border-bottom: 1px solid #44475A; }} th {{ position: sticky; top: 0; background: {BG};
 cursor: pointer; white-space: nowrap; }} tr.win {{ background: #38534d; }}
tr:hover {{ background: #44475A; }} .controls {{ margin: 20px 0; }}
</style></head><body><main>
<nav><a href="index.html">All years</a></nav><h1>Search all Game Awards nominees, 2014–2025</h1>
<div class="note">Released uses the sourced award-year date where available, otherwise the
 earliest documented public release. Partial year/month-only dates appear as partial values
 here but are excluded from weekly and monthly charts. A blank means no applicable game
 release was found; withdrawn nominations remain searchable.</div>
<div class="filters"><label for="search">Search</label><input id="search" type="search"
 placeholder="Name, category, year, release date…" autocomplete="off">
<label for="year">Year</label><select id="year"><option value="">All years</option>{years}</select>
<label for="won">Won</label><select id="won"><option value="">All</option>
<option value="true">True</option><option value="false">False</option></select></div>
<p id="count" aria-live="polite"></p><div class="scroll"><table><thead><tr>
<th data-key="Name">Name ↕</th><th data-key="Category">Category ↕</th>
<th data-key="Year">Year ↕</th><th data-key="Released">Released ↕</th>
<th data-key="Won">Won ↕</th></tr></thead><tbody id="results"></tbody></table></div></main>
<script id="nominees" type="application/json">{payload}</script>
<script>
const rows = JSON.parse(document.getElementById('nominees').textContent);
const search = document.getElementById('search');
const year = document.getElementById('year');
const won = document.getElementById('won');
const tbody = document.getElementById('results');
let sortKey = 'Year', descending = false;
function render() {{
 const query = search.value.toLocaleLowerCase().trim();
 const results = rows.filter(row => (!year.value || String(row.Year) === year.value) &&
   (!won.value || String(row.Won) === won.value) &&
   (!query || [row.Name,row.Category,row.Year,row.Released,row.Won,row.Status]
      .some(value => String(value).toLocaleLowerCase().includes(query))));
 results.sort((a,b) => {{
   const x = a[sortKey], y = b[sortKey];
   const comparison = x < y ? -1 : x > y ? 1 : 0;
   return descending ? -comparison : comparison;
 }});
 tbody.replaceChildren();
 const fragment = document.createDocumentFragment();
 for (const row of results) {{
   const tr = document.createElement('tr');
   if (row.Won) tr.className = 'win';
   for (const key of ['Name','Category','Year','Released','Won']) {{
     const td = document.createElement('td');
     td.textContent = key === 'Won' ? String(row.Won).replace(/^./, x=>x.toUpperCase()) : row[key];
     if (key === 'Released') td.title = row.ReleaseBasis;
     if (key === 'Name' && row.Status === 'withdrawn') td.title = 'Withdrawn nomination';
     tr.appendChild(td);
   }}
   fragment.appendChild(tr);
 }}
 tbody.appendChild(fragment);
 document.getElementById('count').textContent = `Showing ${{results.length}} of ${{rows.length}} nominations`;
}}
for (const control of [search, year, won]) control.addEventListener('input', render);
for (const th of document.querySelectorAll('th[data-key]')) th.addEventListener('click', () => {{
 const key = th.dataset.key;
 descending = sortKey === key ? !descending : false;
 sortKey = key;
 render();
}});
render();
</script></body></html>"""
    (OUTPUT / "nominees.html").write_text(page, encoding="utf-8")


def main():
    nominations, categories, ceremonies = clean_data()
    OUTPUT.mkdir(exist_ok=True)
    assets = OUTPUT / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
    write_table(nominations)

    homepage = []
    for year in sorted(ceremonies):
        folder = OUTPUT / f"f_{year}"
        folder.mkdir(exist_ok=True)
        ceremony = ceremonies[year]
        year_rows = nominations.filter(pl.col("year") == year)
        # The annual distribution concerns games available by the ceremony,
        # not future releases recognized by Most Anticipated.
        annual_rows = year_rows.filter(
            (pl.col("nomination_status") == "active") &
            (pl.col("category_type") != "unreleased_game") &
            (pl.col("released_date").is_null() |
             (pl.col("released_date") <= date.fromisoformat(ceremony["ceremony_date"])))
        )
        plot(annual_rows, ceremony, "week", f"{year} · All game nominations by release week",
             folder / "all_categories_week.html", annual=True)

        links = ["<div class='card'><a href='all_categories_week.html'>All game nominations · release week</a></div>"]
        year_categories = categories.filter(pl.col("year") == str(year)).to_dicts()
        for category in year_categories:
            title = category["category"]
            category_rows = year_rows.filter(pl.col("category_id") == category["category_id"])
            stem = f"{category['category_id']}_{slug(title)}"
            for period in ("month", "week"):
                plot(category_rows, ceremony, period, f"{year} · {title} · Release {period}",
                     folder / f"{stem}_{period}.html")
            # Count any withdrawn entrants in the index even though charts
            # exclude them, so no nomination quietly disappears.
            links.append(f"<div class='card'><strong>{html.escape(title)}</strong> "
                         f"<span class='muted'>({category_rows.height} listed)</span> · "
                         f"<a href='{stem}_month.html'>Monthly</a> · "
                         f"<a href='{stem}_week.html'>Weekly</a></div>")
        (folder / "index.html").write_text(
            "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{year} figures</title>"
            f"<style>{CSS}</style></head><body><main>"
            "<nav><a href='../index.html'>All years</a> · <a href='../nominees.html'>Search nominees</a></nav>"
            f"<h1>{year} descriptive figures</h1><p>{len(year_categories)} categories; "
            f"{year_rows.height} nomination records. Calendar release dates are retained across years.</p>"
            + "".join(links) + "</main></body></html>", encoding="utf-8")
        homepage.append(f"<div class='card'><a href='f_{year}/index.html'>{year}</a> · "
                        f"{len(year_categories)} categories · {year_rows.height} nominations</div>")
        print(f"{year}: {len(year_categories) * 2 + 1} figures", flush=True)
    (OUTPUT / "index.html").write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Game Awards descriptive figures</title><style>{CSS}</style></head>"
        "<body><main><h1>Game Awards descriptive figures · 2014–2025</h1>"
        "<p><a href='nominees.html'>Search the complete nominee table</a></p>"
        "<p>Each year includes a weekly overview and monthly/weekly figures for every category. "
        "Dates before the award year remain on their original calendar dates; consult the notes beneath each figure.</p>"
        + "".join(homepage) + "</main></body></html>", encoding="utf-8")
    print(f"Created {categories.height * 2 + 12} figures, 12 year indexes, and a searchable table in {OUTPUT}")


if __name__ == "__main__":
    main()
