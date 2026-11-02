# Phase 1 — infrastructure feasibility

This branch is intentionally **not** a working Marketplace monitor.

## Current scope
- A **manual-only** GitHub Actions workflow verifies Python/Playwright/Chromium on a hosted Linux runner.
- No hourly schedule, Facebook authentication, scraping, Telegram token, database or dashboard.
- Example search settings are non-secret placeholders.

## Run
1. Review this branch and merge it into main when ready (GitHub Actions manual workflows generally need to be on the default branch to appear in the Actions tab).
2. Open Actions > Marketplace feasibility - manual only > Run workflow.
3. Confirm the log prints `PASS: Chromium launched on GitHub Actions`.

## Next gate
Review the source and license of an existing open-source monitor, confirm Meta terms and account security, then test whether legitimate Marketplace data retrieval works in a hosted environment. Do not upload Facebook passwords or browser cookies to a public repository. GitHub Secrets are not a guarantee against account risk.

## Later gates
1. Telegram notification test using a test message.
2. Durable seen-ID state and first-run baseline.
3. Limited hourly schedule with timeout and concurrency control.
4. Mobile dashboard after the retrieval method is proven.

## Important
A passing browser smoke test proves only that Chromium starts. It does **not** prove Facebook Marketplace scraping works.
