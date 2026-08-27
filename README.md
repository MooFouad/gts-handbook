# app.gts guide

A self-contained, bilingual (EN/AR) visual handbook for the GTS HR Intranet (`app.gts.sa`) — a slide deck walking new employees through sign-in and every dashboard tab, built from real screenshots of the live app.

**Live file:** open [`handbook.html`](./handbook.html) directly in a browser — no server or build step needed to view it.

## How it's built

1. **`capture.js`** (Playwright) — launches a fresh Chrome profile, captures the login pages logged-out, then waits for a manual login before capturing every dashboard tab as a full-page, high-resolution screenshot. Raw output goes to `captures/` (git-ignored — contains unblurred personal data, never committed).
2. **`build_captures.py`** — downscales the raw captures, blurs only genuinely sensitive regions (salary figures, phone/personal email, payment beneficiary/amount), and writes everything into `imgmanifest.json` as base64 data URIs.
3. **`build.py`** — merges `deck.template.html` (the editable source: layout, styles, per-slide copy) with `imgmanifest.json` into the final self-contained `handbook.html`.

```bash
npm install            # installs Playwright
node capture.js        # re-capture live screenshots (needs a real login)
python build_captures.py
python build.py         # -> handbook.html
```

## Notes

- Sensitive data (salary amounts, personal phone/email) is blurred in the images baked into `handbook.html` — never captured unblurred in anything that's committed.
- `captures/` (raw screenshots) and `node_modules/` are git-ignored on purpose.
