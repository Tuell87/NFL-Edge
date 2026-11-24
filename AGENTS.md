# NFL Edge repository instructions

Run [Ship Check](.agents/skills/ship-check/SKILL.md) before reporting that development work is finished, or when the owner asks for an end-of-work audit. Report its findings and next steps. Landing requires the owner's explicit approval.

NFL Edge identifies a release by its commit SHA in `data/research_status.json`. Use the SHA in place of a separate version bump. For new changes, keep the change summary and verification checklist in the pull request. Record the tested commit when known and distinguish pre-push tests from GitHub checks. For existing branches, apply the release rules that were documented when the work was done.

Use GitHub `origin/main` as the shared source of truth. Check a separate shared checkout if the owner identifies one. Compare the live Pages release independently.
