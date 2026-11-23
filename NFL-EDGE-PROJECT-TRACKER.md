# NFL-Edge 2.0 — Living Engineering Tracker

Updated: 2026-11-23. Repository: https://github.com/Tuell87/NFL-Edge. Mobile site: https://tuell87.github.io/NFL-Edge/.

## Current product status

**Research-only NFL player-prop analysis site. No validated betting recommendations or game-day active verification.** The site collects ESPN public game/box-score and roster-listing snapshots and optionally FanDuel odds via server-side The Odds API. Live GitHub Pages deployment checks have passed, but the newest build must be checked by commit SHA; a successful PR test does not verify a live deployment. Public roster listing is not injury clearance or game-day active status.

The project includes descriptive player baselines, chronological and season-separated yardage comparisons, held-out Brier/calibration research, opponent-context research, data-integrity gates, mobile dashboards, and read-only deployment health. No historical win rate or profit edge is established.

## Source and reliability limitations

- **Historical ESPN box scores:** Rolling recent-game collection plus independently cached 2024 and 2025 NFL season archives. Archived seasons are bounded, may have missing summaries, and are not certified complete. Never interpret a count of collected games as full schedule coverage.
- **Archives:** Reject wrong-season events and impossible counts. Cache only archives meeting coverage thresholds. Merge complete event groups without duplicates, with an 80,000-row cap. Recent sample cache is saved before archive merging, preventing stale mixed-source restoration.
- **Roster:** ESPN team listing is a point-in-time identity cross-check, **not** proof of active, injury-free, or expected playing status.
- **Odds:** The Odds API FanDuel sample covers at most two upcoming events. The event-odds collector reads each market's published update time. Missing timestamps remain unknown and fail the research freshness gate. The optional server-side key may be missing, and prices can change. No sportsbook handoff is connected.
- **Model:** Historical over probabilities and opponent-context factors are uncalibrated research. The readiness gate always sets `prediction_ready: false` and market audit `recommended: false`.
- **Evaluation:** Rolling dates and season-separated training tests are retrospective, may have incomplete selection and correlated observations. Opponent ratios can reflect usage and opponent schedule, not necessarily defensive strength.

## Current engineering priorities

1. **P0: Production correctness:** Verify latest main deployment with exact release SHA, archive coverage, data freshness, and UI smoke tests; fix deployment failures before further modeling.
2. **P0: Data identity and coverage:** Confirm ESPN roster parser against live responses, improve player/team/market reconciliation, quantify archive gaps, and avoid silent missing-data assumptions.
3. **P1: Independent availability:** Evaluate a reliable, permission-appropriate source for injury designations and official game-day inactives. Separate reported status from verified active; do not automatically promote predictions.
4. **P1: Historical market data:** Store immutable, timestamped pre-kickoff sportsbook lines and forecasts before claiming value or backtest ROI.
5. **P2: Calibration and opponent research:** Evaluate per-market, per-line, per-season Brier/log loss, MAE, uncertainty and prospective lift versus market-only baselines. Retain `research_only` until evidence is sufficient.
6. **P3: Product polish:** Consolidate old duplicate pages, improve mobile load time and accessibility, and document data contracts and collector operations.
7. **P4: Parlay simulation:** Only after independently validated single-leg probabilities and correlation models; no naive independence claims.

## Recent verified work

| PR | Outcome |
|---|---|
| #47 | Frozen pre-season opponent-model evaluation |
| #48 | 2025 ESPN archive collection and complete-game merge |
| #49 | Mobile research-readiness summary |
| #50 | Archive validation and cache integrity |
| #51 | 2024 archive and three-season research collection |
| #52 | Indexed, leakage-safe opponent-model lookups |
| #53 | Raw-history cache separation, larger merge cap, corrected coverage denominator |
| #54 | Exact deployed commit verification and stronger JSON contracts |
| #62 | FanDuel market eligibility diagnostics distinguish unsupported prop types from other join failures |
| #63 | 2025 archive restore and save cache keys aligned |
| #64–#66 | Five-tab homepage, compact player statistics, and deduplicated Research links |

All listed PRs passed pull-request CI and were merged. Live deployment is verified separately through the Pages workflow.

The FanDuel odds page displays 20 selections per page, with player and market filters, feed and bookmaker timestamps, and a game-started label for past kickoff times.

### Scoreboard and FanDuel coverage

Release `5969347` published 118 outcomes. The audit filtered 56 anytime touchdown selections and 31 unders, then rejected all 31 supported overs at the freshness check. The published outcome timestamps were all missing. [The Odds API event-odds schema](https://the-odds-api.com/liveapi/guides/v4/index.html#get-event-odds) places `last_update` on each market. The collector now reads that field. A fresh timestamp only clears the freshness check. Player identity, teams and sufficient historical samples are still required.

Release `3e380f4` restored timestamps for all 118 outcomes and made 17 of 31 supported overs eligible for research comparison. All 14 remaining selections were from Packers–Rams, a game beyond the default ESPN scoreboard week. The scoreboard collector now uses ESPN calendar metadata to include pregame events from the next listed week with one additional request. The current scoreboard remains available if the next-week request fails.

## Project structure

- `.github/workflows/pages.yml` — CI, ESPN/odds collection, data evaluation, safety gates, static Pages publishing and live checks.
- `scripts/fetch_*.py` — bounded source collectors; `scripts/check_season_archive.py` and `scripts/merge_season_archive.py` validate and combine seasons.
- `scripts/build_*.py`, `scripts/evaluate_*.py` — descriptive stats, matchup joins, calibration and research-only comparisons.
- `scripts/check_data_contracts.py`, `scripts/check_generated_health.py`, `scripts/check_live_pages.py` — build and deployed-site safety checks.
- `tests/` — Python offline regression tests and Node UI smoke tests.
- `index.html` — game-day homepage; `dashboard.html` — read-only GitHub command center; other HTML pages are focused research views.
- `data/*.json` — generated in GitHub Actions, not hand-edited model outputs.

## Workflow and acceptance criteria

For each change: inspect current code, add tests for the failure, create a branch and PR, require successful verify CI, squash merge, then verify the actual main-branch deployment and published commit. Never report PR success as production success. Keep release notes and this tracker current. Avoid claiming that an injury/roster source proves player participation or that retrospective accuracy establishes betting profitability.

## User review needed

- Whether to remove the legacy 134 KB `nfl-edge-terminal.html`, `home-next.html`, and demo pages after preserving any desired features.
- Whether to pay for broader historical odds, injury/inactives and player-opportunity data.
- Which specific prop markets and sportsbooks to prioritize once trustworthy inputs exist.
