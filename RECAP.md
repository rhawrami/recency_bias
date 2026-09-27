# Game Awards recency-bias study: progress recap

## Research question

Do games released closer to The Game Awards voting period have an advantage?
So far, the analysis compares **winners with other nominees in the same award
category**. It does not yet compare nominees with the universe of all eligible
games, or establish why individual jurors or fans voted as they did.

## Dataset assembled

- **2014–2025:** 12 ceremonies, 354 category-years, and 1,774 nomination
  records. Winners, category types, withdrawals, associated games, dates,
  provenance and release-date precision are recorded in
  [`data/nominations.csv`](data/nominations.csv),
  [`data/categories.csv`](data/categories.csv), and
  [`data/ceremonies.csv`](data/ceremonies.csv).
- Historic nominees come from annual ceremony lists, checked against
  [official historical winners](data/official_winners.csv). The
  [2025 official nominees](data/official_nominees_2025.csv) are preserved
  separately. The 2025 *Megabonk* Debut Indie nomination is marked withdrawn.
- Release-date records and alternate platform/region launches are retained in
  [`data/release_events.csv`](data/release_events.csv). The main nomination
  table distinguishes earliest public release from a documented release of
  the version relevant to that award year. Several misleading base-game,
  early-access, port, remake and VR dates were corrected with cited overrides;
  the underlying claims remain available for audit.
- Nominee-level vote totals are **not publicly available** in the sources
  checked. The count field is intentionally blank rather than guessed.

### Voting chronology

[`data/voting_timeline.csv`](data/voting_timeline.csv) separates jury nominee
ballots, jury winner ballots, standard public voting, early fan-selected
awards, and the separate Players' Voice rounds. Each known endpoint has source
wording, a URL and a confidence label. A report that voting was *already open
by* a date is recorded separately from a documented opening date.

- Full **website** public-voting start/end days are documented for **2017**
  and **2024**; the 2024 organizer notice specifies a December 11 close at
  6 p.m. Pacific. The **2018 Discord** voting window (November 13–December 5)
  is documented separately and is not assumed to be the website window.
- Voting was reported open by nominee-announcement day in **2018–2023 and
  2025**, without proving the precise website opening instant. Public-vote
  closing days are documented for 2020–2025. The 2018–2019 website closing
  dates and 2014–2016 fan-voting windows remain unverified.
- The **2020 jury nomination** ballot was sent October 29, due November 6,
  with updates permitted through November 13. In **2024**, those ballots
  were due November 12, before the November 22 game-eligibility cutoff.

## Descriptive output

Open [`docs/index.html`](docs/index.html) to
browse **720 offline Plotly figures**: monthly and weekly release histograms
for every category-year and one weekly overview per year. Winning-release
bins are highlighted; annual weekly bars show winner counts. Documented
website voting endpoints have dotted lines, with uncertain bounds explained
in figure notes. The [searchable nominee table](docs/nominees.html)
contains all 1,774 rows, including withdrawn nominees. Figures use the
requested dark/pastel palette and Palatino font.

The initial [`average release-to-vote gaps`](data/avg_release_lags.csv)
calculate days between the release date and a website voting-date reference
for all game-associated nominations versus winning nominations. These are
row-level averages: a game nominated in multiple categories appears multiple
times. The [coverage file](data/avg_release_lags_coverage.csv) distinguishes
documented openings (2017, 2024), dates on which voting was observed open,
and a **low-confidence nominee-announcement-date assumption for 2014–2016**.
Those early assumed dates should not be treated as verified voting openings.

## Within-category results

The primary descriptive measure in
[`data/category_release_diffs.csv`](data/category_release_diffs.csv) is:

> **winner release date − average release date of the other nominees**, in days

**Positive** means the winner released later. Each category with a dated
winner and at least one dated non-winner contributes one comparison. Non-game
awards, Most Anticipated, withdrawn nominations, missing day-level dates and
post-ceremony releases are not compared. **269 of 354** category-years have a
usable gap. The [annual result](data/year_category_release_diffs.csv) is an
arithmetic mean of those gaps, **weighting each category equally**. This
within-category comparison needs no voting-opening-date assumption: a common
voting date cancels from the difference.

### Game of the Year versus other awards

| Group | Usable categories | Mean gap (days) | Median gap (days) | Winner released later |
| --- | ---: | ---: | ---: | ---: |
| Game of the Year | 12 | −37.0 | −68.3 | 3/12 |
| All non-GOTY game awards | 257 | +33.8 | +40.5 | 160/257 |
| Other standard game awards¹ | 223 | +52.1 | +40.5 | 139/223 |

¹ The standard-award sensitivity group sets aside Best Ongoing, Best
Community Support, Best Esports Game and Players' Voice. These awards' older
live-service titles or distinct public bracket make original launch dates
and voting procedures less comparable. They are still retained and summarized
as separate groups in [`data/goty_vs_non_goty_overall.csv`](data/goty_vs_non_goty_overall.csv).

The standard non-GOTY annual mean is greater than the GOTY gap in **9 of 12
years**; the [year-by-year comparisons](data/goty_vs_non_goty_by_year.csv) show
the exceptions. The focused [GOTY table](data/goty_release_diffs.csv) includes
each winner's release date, gap, and rank among its year's nominees. In GOTY,
winners were generally *earlier* than the other nominees' average. In other
standard categories, the later-winner pattern is more common. This is
consistent with investigating whether less prominent awards are more prone
to recency effects, **not proof of a voter's motivation**. In particular,
winner choices are mostly determined by juries rather than public votes in
recent years, games can appear in multiple categories, and older recurring
games create long-tailed gaps.

## Key limits and next work

1. Build the **full eligible-game population**, including games with no
   nomination, to test recency at the *nomination* stage. The current results
   concern winners conditional on already being nominated.
2. Audit award-specific dates beyond the documented overrides (regional
   releases, remasters, DLC, seasons and early access). An original launch
   may be years before the work recognized by an ongoing-game award.
3. Compare robust category-level measures, such as winner release-date ranks
   and medians, and test sensitivity to recurring-game categories and titles
   receiving multiple nominations. Twelve GOTY outcomes are a small sample;
   treat cross-year patterns as descriptive until those checks are done.
4. Continue sourcing historical voting and jury deadlines. Do not turn an
   observed-open-by date into a purported exact opening date.

## Reproducibility

See [`README.md`](README.md) for setup, file definitions, caveats and the
ordered rebuild/validation commands. The relevant calculation scripts are
[`scripts/calculate_category_release_diffs.py`](scripts/calculate_category_release_diffs.py),
[`scripts/calculate_goty_release_diffs.py`](scripts/calculate_goty_release_diffs.py),
and [`scripts/compare_goty_non_goty.py`](scripts/compare_goty_non_goty.py).
