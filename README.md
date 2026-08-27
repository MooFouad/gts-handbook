# app.gts guide

A bilingual (EN/AR) visual handbook for the GTS HR Intranet (`app.gts.sa`) — a slide deck walking new employees through sign-in and every dashboard tab, built from real screenshots of the live app.

**Live file:** [`handbook.html`](./handbook.html) — a tiny (~25KB) shell that loads each slide's screenshot from `img/` on demand, so the page opens instantly instead of downloading everything up front.

## How it's built

1. **`capture.js`** (Playwright) — launches a fresh Chrome profile, captures the login pages logged-out, then waits for a manual login before capturing every dashboard tab as a full-page, high-resolution screenshot. Raw output goes to `captures/` (git-ignored — contains unblurred personal data, never committed).
2. **`build_captures.py`** — downscales the raw captures, blurs only genuinely sensitive regions (salary figures, phone/personal email, payment beneficiary/amount), and writes real JPG files (plus the logo/favicon) into `img/`.
3. **`build.py`** — copies `deck.template.html` (the editable source: layout, styles, per-slide copy, `img/...` references) to `handbook.html`.

```bash
npm install            # installs Playwright
node capture.js        # re-capture live screenshots (needs a real login)
python build_captures.py
python build.py         # -> handbook.html
```

## Notes

- Sensitive data (salary amounts, personal phone/email) is blurred in the images in `img/` — never captured unblurred in anything that's committed.
- `img/` is tracked in git (it's the processed, blurred deliverable). `captures/` (raw screenshots) and `node_modules/` are git-ignored on purpose.
