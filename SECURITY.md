# NFL-Edge security and deployment boundaries

Updated: 2026-11-23.

NFL-Edge is a **public, static, research-only** NFL player-prop analysis site. GitHub Pages publishes selected HTML and generated JSON through the explicit allowlist in `.github/workflows/pages.yml`. It is **not** a verified sportsbook prediction or betslip integration.

## Credentials and provider data

- Keep `ODDS_API_KEY` only in GitHub Actions secrets. The server-side collector requests The Odds API and publishes sanitized, bounded FanDuel odds JSON without a key.
- Never commit keys, tokens, private account information, `.env`, `credentials.json`, or `secrets.json`.
- The legacy **`nfl-edge-terminal.html` is not approved for publication**. It stores a user-entered odds key in browser localStorage and calls the provider directly. Do not link, copy, or deploy it. It is retained in source pending a deliberate migration/removal decision.
- Release checks scan all HTML files copied by the Pages allowlist and reject direct browser odds-provider calls, external script sources, and accidental terminal publication.
- Public JSON snapshots contain research data, not access tokens or verified medical/injury clearance.

## Deployment verification

PR CI checks static release rules, Python tests, Node UI smoke tests and Python compilation. Main-branch deploy jobs collect data, validate JSON and readiness, publish the static allowlist, then check the **actual published Pages release SHA**. PR CI passing is not evidence that a new Pages deployment is live.

The prediction gate intentionally refuses verified game-day availability and betting recommendations until independent sources and calibration are established. Do not remove these blockers to make a dashboard look complete.

## Operating guidance

Use GitHub 2FA, secret scanning/push protection and protected branches with required checks when available. Review new provider endpoints, license restrictions, HTML injection surfaces and data retention before production. Release checks are useful safeguards, **not** a comprehensive penetration test or security certification.
