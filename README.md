# Recency bias in the Game Awards

Nominee-level datasets for the **2014–2025** Game Awards, including the
categories, winners, dated game releases and ceremony-year rules. This is the
awards dataset; a universe of all eligible but un-nominated games has not yet
been assembled.

## Data

| File | Grain and purpose |
| --- | --- |
| `data/ceremonies.csv` | One ceremony per year: announcements, eligibility cutoffs, documented website-voting dates, separately labeled observed-open bounds, jury-ballot dates and rules. |
| `data/voting_timeline.csv` | One row per year, voting clock, channel and bracket round. Each endpoint includes quoted wording, URL, source type, confidence, date and any reported time zone. |
| `data/categories.csv` | One category per year, retaining the historical name and whether the award is for a game, performance, person, adaptation, other entity or honorary recipient. |
| `data/nominations.csv` | One nominee per category-year, including `is_winner`, source, optional associated game and release dates. `nomination_status=withdrawn` marks the 2025 Megabonk nomination, removed after announcement. |
| `data/release_events.csv` | All retrieved Wikidata P577 release claims, including precision, platform and place identifiers when present, and claim IDs. Multiple records for one game are expected. |
| `data/official_winners.csv` | Independently scraped winners from official year-by-year Rewind pages (2014–2024) and official 2025 category pages and Players' Voice. The site does not currently serve the 2025 Rewind page. |
| `data/official_nominees_2025.csv` | Currently displayed nominees on each official 2025 category page and the Players' Voice final-round bracket; withdrawn entries do not appear here. |
| `data/source_revisions.csv` | Wikipedia article revision IDs and retrieval timestamps for the annual nominee lists. |

`is_winner` is 1/0; for honorary awards, several recipients can be winners.
`nominee_order` records the **source's presentation order** (winner first),
not a vote ranking. Blank `game_title` means the award has no associated game.
`vote_count` is blank because per-nominee jury and public vote totals have not
been published; a site's “Votes cast 0/29” refers to the visitor's own ballot.

The date fields in `nominations.csv` deliberately distinguish:

- `original_release_date`: earliest **day-precision** public release claim
  for that title (falling back to month/year precision only if necessary).
  This may be early access, an overseas launch, or an outdated Wikidata entry.
- `award_year_release_date`: a day-precision original release in that award
  year, or a small number of explicitly sourced later releases (2014 North
  American *Bravely Default*, 2014 *GTA V* remaster, 2023 full *Baldur's Gate
  3*, and 2025 full *Hades II*). Blank otherwise; it is **not** proof the game
  was ineligible. Basis and source are recorded in adjacent columns.
- `release_events.csv`: inspect all dates and platform/region qualifiers before
  deciding which release matters for any particular category and year.

Curated first-release corrections are recorded for *Bayonetta 2* (a pre-release
Nintendo Direct was listed as a release), *Block'hood* (2016 early access),
*The King of Fighters XIV* (2016 console before 2017 PC), and *Monster Hunter
World: Iceborne* (2019 console before 2020 PC). Original Wikidata claims
remain visible in `release_events.csv` for audit.
Additional sourced corrections cover day-precision dates for *Valiant Hearts:
The Great War*, *Overcooked 2*, *Beat Saber* (2018 early access, 2019 full
release), and *Umamusume: Pretty Derby* (2021 Japanese launch, 2025 worldwide
launch). See the source and release-basis columns for each nomination.
For the 2014 fighting category, dated award-year versions are also recorded
for *Killer Instinct: Season Two*, *Persona 4 Arena Ultimax* and *Ultra Street
Fighter IV*; the 3DS launch of *Super Smash Bros.* has a day-precision source.
Other award-specific version dates cover *Rez Infinite* (2016 VR edition),
the 2021 *Nier Replicant* remaster and *Resident Evil 4* VR edition, 2023
*Resident Evil Village* and *Gran Turismo 7* VR modes, and 2024 *Arizona
Sunshine Remake*. Base-game launch dates would otherwise dominate their
category comparisons even though the nominated work was newer.
For Game of the Year, *Persona 5* uses its 2017 worldwide release and *Hades*
its 2020 full release (their earlier Japan/early-access launches remain in
`original_release_date`).

Especially for Best Ongoing, Best Community Support, remakes and DLC, neither
the original title launch nor the most recent port necessarily dates the work
being judged. Do not silently substitute one for the other.

## Rebuild and check

Install Python 3 and `pip install -r requirements.txt`, then run:

```sh
python3 scripts/build_awards.py
python3 scripts/enrich_releases.py
python3 scripts/build_ceremonies.py
python3 scripts/calculate_release_lags.py
python3 scripts/calculate_category_release_diffs.py
python3 scripts/calculate_goty_release_diffs.py
python3 scripts/compare_goty_non_goty.py
python3 scripts/validate.py
python3 scripts/build_descriptive_figures.py
python3 scripts/validate_descriptive_figures.py
python3 scripts/validate_category_release_diffs.py
python3 scripts/validate_non_goty_comparison.py
```

The first script gathers [annual ceremony nominee tables](https://en.wikipedia.org/wiki/The_Game_Awards_2014)
and [official Rewind winners](https://thegameawards.com/rewind/year-2014).
The second joins the nominated titles to [Wikidata release-date claims](https://www.wikidata.org/wiki/Property:P577)
and caches lookups locally in an ignored checkpoint; rebuilding nominations
alone clears the enrichment until the second command runs again. The year
metadata and voting-clock ledger are explicitly curated from dated notices,
participating jury outlets, contemporary reports and annual ceremony articles.
The live [Game Awards FAQ](https://thegameawards.com/faq)
describes current rules, not necessarily each historical year.

### Reading the voting dates

The ledger separates `jury_nominations`, `jury_winners`, `public_winners`,
`public_fan_choice` (early fan-selected categories) and the independent
`players_voice` bracket. Website and Discord voting can have distinct dates.
An `open_date` is populated only when a source explicitly states a start day;
`first_observed_open_date` instead means a dated report said voting was **already
open by then**. It is a bound, not an exact launch time. `close_date` is never
filled from the ceremony date or from another channel's window. Confidence is
`documented_primary` (organizer notice), `documented_secondary` (dated report
or cited annual account), `observed_by`, or `unknown`. A time zone accompanies
an endpoint only when its time of day is stated; `America/Los_Angeles` records
sources specifying “PT”. Dates without a clock time have no inferred hour.

For ordinary voting on the awards website, **2017 and 2024 have documented
start and end days**. Reports show voting already open by nomination day in
2018–2023 and 2025, but do not prove those exact start times. The 2018
**Discord** window (Nov 13–Dec 5) is sourced separately; it is not copied
into the website close field. The website close remains unverified in 2018
and 2019; early years 2014–2016 have no confirmed fan-vote window. The
2020 jury nomination ballot was sent Oct 29, due Nov 6, with updates accepted
through Nov 13. In 2024, nomination ballots were due Nov 12, preceding the
Nov 22 game-eligibility cutoff. Players' Voice dates and 2025 rounds are
recorded in their own rows. Unknown dates remain blank.

## Descriptive figures and table

Open [`docs/index.html`](docs/index.html) in a
browser. Each `f_{year}/` directory has an index, a release-month and
release-week histogram for **every category**, and a weekly histogram across
that year's game-associated nominations. All pages use one local shared
Plotly bundle (`docs/assets/plotly.min.js`), so the figures
work offline. [`docs/nominees.html`](docs/nominees.html)
is a client-side searchable, sortable table of all 1,774 nominations with
Name, Category, Year, Released, and Won (True/False); it also includes the
withdrawn 2025 nomination. Regenerate all figures with
`python3 scripts/build_descriptive_figures.py` after changing the CSVs.

### Publish with GitHub Pages

The generated `docs/` directory is the complete static site. In the GitHub
repository settings, open **Pages**, select **Deploy from a branch**, choose
the default branch and **/docs** as the folder, and save. Commit and push the
generated `docs/` files (including `assets/` and every `f_{year}/` directory).
The site will be available at
`https://rhawrami.github.io/recency_bias/`, with the nominee table at
`https://rhawrami.github.io/recency_bias/nominees.html` and individual year
indexes at `https://rhawrami.github.io/recency_bias/f_2025/` (for example).
The `/docs` segment is a repository folder, not part of the published URL.

The plots use calendar month and Monday-starting calendar week, including
the **release year** so an older December release is not mistaken for a new
one. Pink marks any bin containing a winning nomination; the annual plot
labels every bar with its winning-nomination count. Bars use the active
nominee rows (the annual plot excludes Most Anticipated and future releases),
not distinct games. Games can appear in multiple award categories and
actors can generate multiple nominations for one game. Missing and partial
release dates are never imputed into a month or week; a category with no
plottable game dates still gets two explanatory figures. Dotted voting lines
use only **documented website** opening/closing days from `ceremonies.csv`.
First-observed-open bounds and the 2018 Discord-only closing date appear in
figure notes instead of being presented as exact website endpoints. Every
figure carries caveats for missing dates, old releases and other relevant
eligibility issues. Read the figure notes before interpreting the histograms
as recency-bias evidence.

### Average release-to-vote gaps

`data/avg_release_lags.csv` has the three-column annual result: Award year,
`avg_diff_all`, and `avg_diff_winners`. Positive values are the mean number of
calendar days **from release until the public-vote date**; a negative value
would mean a release after that date. Use `python3 scripts/calculate_release_lags.py`
to rebuild it. `data/avg_release_lags_coverage.csv` contains the voting date
used, confidence basis and sample sizes for each mean.

For **2017 and 2024**, the voting date is a documented website opening date.
For **2018–2023 and 2025**, it is the day contemporary reporting found voting
already open, which might be *later* than the actual opening. For **2014–2016**,
no public-voting date was verified: the nominee-announcement day is explicitly
used as a **low-confidence assumption**, not represented as a documented fact
in `data/ceremonies.csv` or the figures. These three cohorts should not be
treated as having measured opening dates.

Each observation is an **active nominee-category entry with an associated
game and a day-precision release**. Most Anticipated, non-game awards,
withdrawn nominees, missing/partial release dates and releases after the
ceremony are excluded; games may still be released *after public voting opens*
if they were eligible that year. A game nominated or winning in multiple
categories contributes multiple observations. When available, the sourced
award-year release is used, otherwise the first documented public launch;
for older ongoing games and updates this can be years before the work being
recognized. These means are descriptive, not a causal estimate of bias.

### Winner-versus-nominees comparison within each category

`data/category_release_diffs.csv` contains **one row for every category-year**,
with a comparison status and a day gap where the winner and at least one other
nominee have usable dates. The gap is **winner release date minus the mean
release date of the other nominees**, measured in days. Positive means the
winner was released *later* than its competitors; negative means earlier.
Withdrawn nominations, unreleased Most Anticipated titles, non-game categories,
missing day-level dates and releases after the ceremony are not compared. The
table shows how many losing nominees had dates and how many were omitted.

`data/year_category_release_diffs.csv` is the **arithmetic mean of the
available category gaps** each year: every category receives equal weight,
regardless of its nominee count. It also counts categories with winners later
and earlier than the other nominees. The year means are calculated from the
three-decimal category values in the CSV before rounding to one decimal. The
public-vote date cancels within each category, so these comparisons do not
require an assumed opening date for 2014–2016. They still depend on which
release date is relevant, particularly for early access, live-service games
and expansion packs; Players' Voice uses finalists rather than every voter
choice.

For a focused comparison, `data/goty_release_diffs.csv` extracts **Game of the
Year** for each of the 12 ceremonies. It includes the winner's date, the
winner-versus-other-nominee gap, and its release-date rank among that year's
dated nominees (1 = earliest). This uses the same release-date conventions as
the other comparisons. Twelve winner outcomes are a small descriptive sample;
it cannot by itself test whether recently released games were more likely to
be *nominated* for Game of the Year.

`data/goty_vs_non_goty_by_year.csv` and `data/goty_vs_non_goty_overall.csv`
compare these same category gaps for GOTY and other categories. `all_non_goty`
includes every usable non-GOTY game category. `standard_non_goty` excludes
Best Ongoing, Best Community Support, Best Esports Game and Players' Voice:
older live-service games and fully public finalist brackets involve different
release-date and voting processes. The excluded groups are reported separately
in the overall table, not dropped from the source category dataset. Overall
means weight each usable category-year equally; the by-year table also shows
each year's mean and median. Different games can appear in several categories,
and this comparison cannot establish why individual jurors or fans voted as
they did.

## Known source conflicts and coverage limits

- The official [2023 Rewind page](https://thegameawards.com/rewind/year-2023)
  says *Genshin Impact* won Players' Voice. The [contemporary IGN winner
  report](https://www.ign.com/articles/the-game-awards-2023-winners-the-full-list)
  and the annual nominee list identify *Baldur's Gate 3*. The nominee table
  records *Baldur's Gate 3*; both source claims remain visible for audit.
- The official 2025 category page lists **four** Best Debut Indie nominees;
  the historical nominee list also includes *Megabonk*, subsequently
  withdrawn. `nomination_status` preserves that distinction.
- Official winner credits can name a **person or studio** where the annual
  nominee table identifies the associated game (e.g., 2016 Best Game
  Direction, 2025 Best Score and Music). Name mismatches alone are not
  evidence of a different winner; check `official_winners.csv` and the raw
  nominee entry.
- The jury nomination period is distinct from public winner voting; some
  release cutoffs even fall **after** nominee announcements. Several early
  voting dates still require primary-source confirmation. Start-date bounds
  should not be treated as exact starts in analyses.
- Players' Voice rows represent the **finalists** in a multi-round public
  bracket, not every game on the original public ballot. Non-game and honorary
  categories are preserved but not interchangeable with game release dates.
