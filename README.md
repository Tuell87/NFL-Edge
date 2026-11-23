# NFL-Edge 2.0

Mobile-first, **research-only** NFL player-prop data and model evaluation site.

- **Live site:** https://tuell87.github.io/NFL-Edge/
- **Project command center:** https://tuell87.github.io/NFL-Edge/dashboard.html
- **Engineering tracker:** [NFL-EDGE-PROJECT-TRACKER.md](NFL-EDGE-PROJECT-TRACKER.md)
- **CI/deployments:** https://github.com/Tuell87/NFL-Edge/actions

## What it does

The GitHub Actions workflow collects bounded public ESPN game/box-score and roster snapshots, optional FanDuel odds through a server-side The Odds API key, and 2024/2025 historical archives. It builds descriptive player baselines, historical probability and opponent-context research, data-quality reports, and static mobile dashboards. Live Pages verification checks the published release identity and recommendation safety.

**This is not a validated predictive betting system.** ESPN roster listing does not verify active or injury-free status. The Odds API sample is not comprehensive. All experimental prediction readiness is disabled.

## Run offline checks

From the repository root with Python 3 and Node.js installed:

```bash
python3 scripts/check_release.py
python3 -m unittest discover -s tests -p "test_*.py"
node --test tests/*.test.cjs
python3 -m compileall -q scripts tests
```

No API keys are needed for offline tests. Generated `data/*.json` files are produced by the deployment job, not stored in the repository. The Pages deploy job runs on main pushes and its six-hour schedule; PRs only run the verification job.

## Data collection and safety

- `ODDS_API_KEY` is an optional GitHub Actions secret. Never put it in client HTML or commit it.
- Public ESPN endpoints are used for bounded historical and current game/roster snapshots. They can fail or return partial data; the pipeline records coverage and failures.
- Historical archives are cached only after season and coverage checks; game groups merge atomically and preserve source counts.
- `scripts/check_data_contracts.py`, `scripts/check_generated_health.py` and `scripts/check_live_pages.py` enforce generated data safety.
- Model outputs are **research only** and do not produce recommended picks, parlays or verified player availability.

See the tracker for limitations, roadmap and user-review decisions.
