# NFL-Edge 2.0 — Living Project Tracker
Updated: 2026-11-22. iPhone-first development. Repository: https://github.com/Tuell87/NFL-Edge

**Current status:** Mobile static DEMO, not a live or validated NFL prediction engine. PR #1 merged: Pages workflow, static release checks, UI smoke tests, SECURITY.md. Production Pages deployment is **not yet verified**. No live odds, licensed data feed, calibrated model, or verified FanDuel betslip deep link.

## North star
Build calibrated NFL player-prop probabilities, separate **Most Likely** from **Best Value** using timestamped odds and uncertainty, measure every prediction prospectively, and deliver a secure mobile-first interface. No guaranteed outcomes.

## Roadmap
- [ ] **P0 — Deployment:** Confirm GitHub Pages source GitHub Actions; verify both main-branch `verify` and `deploy` jobs; iPhone Safari acceptance test; version and data-freshness labels.
- [ ] **P1 — Data:** License/verify NFL play-by-play, player status/injury, and FanDuel odds coverage; implement secure server-side ingestion and historical odds snapshots; enforce timestamps, normalized IDs, no stale lines, no API keys in client.
- [ ] **P2 — Baselines:** Compare no-vig market baseline, opportunity-adjusted TD count models, and yardage/reception models. Use time-based rolling splits; prevent look-ahead leakage.
- [ ] **P3 — Calibration:** Evaluate Brier score, log loss, reliability by probability/market bucket, sample size, and uncertainty; improve over market-only baseline before promotion.
- [ ] **P4 — Value ranking:** Break-even probability, no-vig assumptions, uncertainty-adjusted EV, line freshness, and conservative pick selection. Show `Most Likely` separately from `Best Value`.
- [ ] **P5 — Ladders/parlays:** Model 1+/2+/3+ TD from one coherent count distribution; test overdispersion; estimate same-game correlation, warn when independence is assumed.
- [ ] **P6 — Product:** Saved forecast snapshots, model versions, performance dashboard, error monitoring, accessibility, mobile performance, verified provider-approved handoff only.

## Accuracy experiments (ranked)
| Priority | Experiment | Validation |
|---|---|---|
| High | Expected opportunity: snaps, routes, carries, targets, red-zone share | Rolling held-out Brier/log loss vs market baseline |
| High | Late injuries, inactive lists, role changes | Timestamped pre-kickoff evaluation; no future data |
| High | Market-derived baseline + closing-line tracking | Incremental lift and CLV, separately from ROI |
| High | Probability calibration by market/odds bucket | Reliability plots, sample counts, proper scoring |
| High | Pace, team total, game script | Feature ablation by market |
| Medium | Weather, opponent, O-line, scheme | Holdout ablation; avoid generic boosts |
| Medium | Negative-binomial / hierarchical TD tails | Held-out 1+/2+/3+ calibration |
| Medium | Ensemble and correlated game simulation | Time-based holdout and correlation calibration |
| Experimental | News/social sentiment | Sourced, timestamped, compared to no-sentiment baseline |

## Scoreboard
Store an append-only **pre-kickoff** record: model version, forecast time, player/game/market/line, bookmaker odds and fetch time, probability, uncertainty, pick decision, and eventual result. Never rewrite history after games.

Primary: Brier, log loss, calibration curves, sample sizes. Secondary: CLV, realized ROI with confidence intervals, latency, coverage. Avoid cherry-picking and claiming profitability from small samples.

## Experiment log
| Date | Hypothesis | Baseline | Variant | Test window / N | Score | Decision |
|---|---|---|---|---|---|---|
| TBD | Opportunity-adjusted TD improves calibration | Market-only | Role + red zone | TBD | Brier/log loss | Not started |

## Release log
| Date | PR | Change | Verification | Deployment |
|---|---|---|---|---|
| 2026-11-22 | #1 | Workflow, checks, tests, security | PR verify passed | Main deploy not yet confirmed |

## Architecture
Licensed feeds → server-side ingestion → normalized historical datastore → feature pipeline → versioned calibrated model → immutable forecast snapshot → API/cache → GitHub Pages iPhone frontend. Pages cannot run a persistent Python backend.

## Immediate next tasks
1. Verify production Pages deployment and iPhone display.
2. Define normalized odds/stats data contract and assess licensed provider coverage.
3. Build reproducible baseline evaluation harness with synthetic fixtures.

## Working agreement
“Continue NFL-Edge using `NFL-EDGE-PROJECT-TRACKER.md` as the plan. Create a branch, make the smallest testable change, run checks, open a PR, explain results and limitations, and update the tracker. Merge only when I approve unless I explicitly authorize auto-merge.”

**Boundary:** All NFL predictions are uncertain. Favor calibration and reproducible evidence over exaggerated confidence.