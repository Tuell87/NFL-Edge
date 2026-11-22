# NFL-Edge deployment security
This repository currently publishes a **demo**, not a live sportsbook prediction engine.
Never commit API keys, access tokens, .env files, credentials, or private customer data.
GitHub Pages is a public static host. Do not call paid odds APIs with a secret in browser JavaScript.
The deployment workflow publishes only index.html and 404.html.
Unverified FanDuel betslip integration stays disabled.
Use GitHub two-factor authentication, secret scanning/push protection where available, and branch rules requiring passing checks.
Changes should be reviewed through pull requests. The release checks are basic safeguards, not a comprehensive security audit.
