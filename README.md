# Apex Investment Strategy

Apex Investment Strategy is an open-source Codex skill for building a local-first momentum investing research workspace.

It can stay lightweight as a strategy explainer, or guide a user step by step into a minimum SQLite database, research backtests, a paper wallet, local Action Packets, and a static web dashboard.

This repository contains no private wallet data, no paid data credentials, no broker integration, and no personal production system state.

## What This Is

- A public Codex skill: `skills/apex-investment-strategy`
- A zero-pip Python toolkit using only the standard library and SQLite
- A local research workflow for price data, momentum signals, backtests, wallet drift, Action Packets, and static dashboard generation
- A starting point users can fork and adapt to their own data and constraints

## What This Is Not

- Not financial advice
- Not a managed portfolio service
- Not a trading bot
- Not connected to any broker API
- Not a copy of any private Apex production wallet, data warehouse, or automation setup

## Install The Skill

From a Codex environment with the skill installer available:

```bash
python scripts/install-skill-from-github.py --repo UltraDD/apex-investment-strategy --path skills/apex-investment-strategy
```

Restart Codex after installation so the skill can be discovered.

## Quick Start From Source

```bash
git clone https://github.com/UltraDD/apex-investment-strategy.git
cd apex-investment-strategy

python skills/apex-investment-strategy/scripts/init_project.py --project-dir ./demo-apex
python skills/apex-investment-strategy/scripts/init_database.py --project-dir ./demo-apex --sample
python skills/apex-investment-strategy/scripts/validate_data.py --project-dir ./demo-apex
python skills/apex-investment-strategy/scripts/run_backtest.py --project-dir ./demo-apex
python skills/apex-investment-strategy/scripts/init_wallet.py --project-dir ./demo-apex --capital 100000
python skills/apex-investment-strategy/scripts/build_action_packet.py --project-dir ./demo-apex
python skills/apex-investment-strategy/scripts/scaffold_web.py --project-dir ./demo-apex
```

Open `demo-apex/web/index.html` in a browser.

## Dependency Model

The baseline has no pip dependencies.

| Layer | Required |
|---|---|
| Skill explanation | Codex skill support |
| Project initialization | Python 3.10+ |
| Database | SQLite via Python standard library |
| Backtest | Python standard library |
| Paper wallet | SQLite via Python standard library |
| Static dashboard | Browser only |
| Advanced dashboard | Bring your own stack if you extend it |

## Minimum Data Requirement

The default momentum settings need enough history:

- Hard minimum: 320 effective trading days per asset
- Practical minimum: 400-500 effective trading days
- Meaningful backtest: 3-5 years or more

CSV schema:

```csv
date,asset_id,close,volume
2024-01-02,sp500,100.0,1000000
```

`volume` is optional for the first public version.

## Repository Layout

```text
skills/apex-investment-strategy/
  SKILL.md
  agents/openai.yaml
  references/
  scripts/
  assets/web-template/
tests/
.github/workflows/ci.yml
```

## Safety

Every generated output is research-only. Use your own judgment, consult qualified professionals for financial decisions, and verify data quality before relying on any signal.

