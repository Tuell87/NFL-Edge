# NFL-Edge codebase audit — 2026-11-23

Scope: GitHub main tree (95 tracked files at audit start), workflow, collectors, evaluators, generated JSON gates, HTML dashboards, Node/Python tests, legacy terminal and open PRs. Findings distinguish **confirmed defects** from **open questions**. PR tests and production deployment are separate evidence.

## Confirmed problems fixed in this audit

| Severity | Problem | Resolution |
|---|---|---|
| High | Daily `data/history.json` cache saved *after* merging old seasons, so a later run could mistake mixed data for a raw current sample | #53: save raw sample before merging; invalidate old cache key; cache only usable raw results |
| High | 50,000-row combined cap admitted only 100 of 285 available 2024 games | #53: 80,000-row cap; 2026-11-23 production subsequently reported **781 games**, including 285 from 2024 and 285 from 2025 |
| High | Historical extraction rate divided combined three-season games by only recent discovered events, potentially exceeding 100% | #53: preserve recent counts separately and compute recent extraction rate against recent discoveries |
| High | Live smoke tests could accept a stale prior deployment with the same JSON keys | #54: embed `GITHUB_SHA` in `research_status.json` and require exact deployed commit |
| Medium | JSON contract missed `windows`, `tests`, `readiness_blockers` types and false-only research readiness | #54: enforce arrays and strict `prediction_ready: false` |
| Medium | Old tracker and security docs described a demo-only, unverified deployment and README contained only a title | #55 and this audit: replace with current, testable documentation |
| Medium | Two abandoned demo-era PRs (#4/#5) remained open and conflicted with current homepage | #55 implements their goals safely; both original PRs closed as superseded |
| Medium | Historical search downloaded every raw multi-season stat row for an eight-game display | #56: compact searchable latest-eight-per-player/category JSON |
| Medium | Zero eligible market comparisons had no explanation despite available odds and matchup rows | #57: per-reason rejection counts, visible on mobile market-audit page |
| Medium | Large legacy terminal stores a browser-side odds API key and calls the provider directly | This audit: ensure it cannot enter the published Pages allowlist; document as unapproved legacy source |

### Verified production observations

2026-11-23 main-branch deployment logs for run `45182120283` reported **781 combined historical games**, including **285 archived 2024 games and 285 archived 2025 games**. Season-separated evaluation produced two retrospective research tests. Cross-feed integrity reported zero warnings and zero errors. The deployed Pages HTTP smoke checks passed. The readiness summary still reported **three blockers** and `research_only`. Later PR merges require their own live deployment verification.

A previous run reported **108 FanDuel odds outcomes**, **67 upcoming player matchups**, and **zero eligible market comparisons**. #57 adds the missing diagnostics; do not infer the cause until its generated data is observed.

## Open items requiring engineering work or user decisions

| Priority | File(s) | Finding and decision needed |
|---|---|---|
| P0 | `scripts/readiness_gate.py`, `scripts/fetch_rosters.py` | No verified official game-day active/inactive and injury clearance source. ESPN team roster membership is **not** sufficient. Select and validate a legal, reliable independent source before enabling predictions. |
| P0 | `scripts/build_market_audit.py`, `scripts/fetch_odds.py` | Real odds feed is capped at two events and has yielded zero eligible research joins. Review new diagnostic counts; then fix only demonstrated player/team/market normalization problems. Do not loosen ambiguity checks. |
| P1 | `scripts/fetch_rosters.py` | Parser assumes ESPN grouped/flat `athletes` and `displayName`; production reports 26 teams with rosters, but some missing teams may be due to schedule scope or endpoint differences. Inspect raw live responses and confirm ID coverage before changing parser. |
| P1 | `scripts/build_baseline.py`, `scripts/evaluate_baseline.py`, `scripts/evaluate_probabilities.py` | Historical duplicate `(event, player, category)` rows are overwritten by dictionary assignment, while `evaluate_opponent.py` rejects ambiguous duplicates. Standardize handling of conflicting duplicates; add cross-model consistency tests. |
| P1 | `scripts/fetch_history.py`, archive collectors | ESPN public coverage is bounded and not a certified complete NFL season. Add schedule completeness checks against independent game lists; preserve failed scoreboard/summary counts. |
| P1 | `scripts/build_research_status.py` | The three permanent readiness blockers should remain visible until independent availability and calibrated model evidence exist. Do not reduce blockers based solely on ESPN roster listing. |
| P2 | `nfl-edge-terminal.html` | **User decision:** 134 KB legacy terminal, direct browser odds-key handling in localStorage, 56 `innerHTML` uses, not deployed. Delete, archive privately, or refactor before any public use. Current workflow must continue excluding it. |
| P2 | `home-next.html`, `legacy-demo.html` | **User decision:** duplicated older homepage and illustrative betslip. Preserve for demos, consolidate, or remove after mobile acceptance testing. No deletion performed. |
| P2 | `data/history.json`, `history.html` | Full raw multi-season JSON remains publicly downloadable for research reproducibility, even though the mobile search now uses a smaller feed. Decide whether to retain public full-history export or publish only compact/aggregated datasets. |
| P2 | `scripts/evaluate_holdout.py`, `scripts/evaluate_opponent_seasons.py` | Retrospective chronological and season-disjoint scores are not a prospective trial, calibrated market odds or proof of profit. Need immutable pre-kickoff predictions and independent-season evaluations. |
| P3 | `.github/workflows/pages.yml` | Several collector/evaluator stages are serialized; expensive ESPN history collection is cached, but run time and API request limits should be monitored as seasons expand. |
| P3 | All UI pages | Automated checks cover text rendering and basic structure, but an actual iPhone Safari accessibility/performance acceptance test has not been performed. |

## Explicitly not changed

- No fabricated player status, odds, or injury clearance.
- No recommendation gate bypass, automatic betting picks, or speculative value rankings.
- No deletion of user-authored legacy pages without review.
- No assumption that passing PR CI proves deployment.
- No claim of full schedule coverage or calibrated predictive performance.

## Next operational checklist

1. Confirm latest main deploy completed and exact `release_sha` matched live Pages.
2. Review #57 diagnostics on `market-audit.html`; investigate the first high-volume rejection reason.
3. Verify actual 2024/2025 archive coverage and missing-game counts independently.
4. Resolve historical duplicate handling consistently across all evaluators.
5. Decide on official injury/inactive data source, legacy terminal removal, and public raw-history retention.
