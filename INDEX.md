# Apex Investment Strategy Index

> Public open-source candidate for the Apex Investment Strategy Codex skill. Read this file before changing project structure.

## Read First

Use this project when working on the public, privacy-safe Apex investment strategy skill and local-first tooling.

Do not use this project for private production wallets, paid data credentials, private local market-data databases, broker integrations, or personal trading logs.

## Overview

This repository packages a public Codex skill plus zero-dependency local scripts. It lets users choose how far they want to go:

- Research-only explanations
- Minimum local SQLite database
- Research backtest
- Paper wallet
- Local Action Packet
- Static web dashboard

## Authority

| Topic | Path | When to read |
|---|---|---|
| Project overview | `README.md` | Public positioning, install, quick start |
| Skill behavior | `skills/apex-investment-strategy/SKILL.md` | Codex invocation and workflow routing |
| Safety boundary | `DISCLAIMER.md` | Financial and tooling disclaimers |
| Python toolkit | `skills/apex-investment-strategy/scripts/` | Local project/database/backtest/wallet/dashboard commands |
| User-facing guides | `skills/apex-investment-strategy/references/` | Layer-specific implementation details |
| Apex alignment guide | `skills/apex-investment-strategy/references/apex-alignment-guide.md` | Helping users grow the public setup toward a 17-asset Apex-like workflow |
| Static dashboard template | `skills/apex-investment-strategy/assets/web-template/` | Frontend scaffold source |
| Tests | `tests/` | Behavior verification |

## Directory Slots

| Slot | Path | Rule |
|---|---|---|
| Entry | `README.md`, `INDEX.md` | Keep public positioning and structure clear |
| Skill | `skills/apex-investment-strategy/` | Must remain installable as a standalone skill |
| Scripts | `skills/apex-investment-strategy/scripts/` | Python standard library only unless a future optional layer is explicit |
| References | `skills/apex-investment-strategy/references/` | Public docs only; no private file paths or personal data |
| Assets | `skills/apex-investment-strategy/assets/` | Templates copied into user projects |
| Tests | `tests/` | Unit and scenario tests for public scripts |
| CI | `.github/workflows/` | Public validation only; no secrets |

## Maintenance Rules

- Keep the baseline dependency-free.
- Keep `--profile apex17` public and privacy-safe: it may scaffold the 17-asset shape, but must not include private production data, credentials, wallets, or broker state.
- Do not commit generated demo workspaces, SQLite files, wallet files, or Action Packet outputs.
- Do not mention or depend on private workspace paths.
- Any new optional layer must be documented as optional in README and SKILL.md.
- Update this index when adding a new long-lived slot.
