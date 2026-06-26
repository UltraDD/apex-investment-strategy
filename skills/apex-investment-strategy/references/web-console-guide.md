# Web Console Guide

The web console is optional and static by default.

Generate it with:

```bash
python scripts/scaffold_web.py --project-dir ./my-apex
```

Output:

- `web/index.html`

The generated page is designed to open directly in a browser. It embeds the latest Action Packet and backtest summary, so no local server is required.

## First Screen

The page should show:

- data status
- current signal
- target weights
- wallet drift
- suggested paper trades
- backtest summary

## Design

The template uses a quiet, Apple-style local tool interface:

- system font stack
- semantic colors
- light and dark mode
- one primary accent
- stable cards and tables
- no marketing hero
- no decorative gradients

## Optional Advanced Frontend

Users can replace the static page with their own React, Next.js, Tauri, or desktop app later. Keep that as an extension, not a default dependency.

