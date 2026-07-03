# Apex Investment Strategy

Apex Investment Strategy is a public Codex skill and local-first Python toolkit for exploring momentum-style investing workflows.

It can stay lightweight as a strategy explainer, or guide a user step by step into a minimum SQLite database, research backtests, a paper wallet, local Action Packets, and a static web dashboard.

This repository is research tooling only. It contains no private wallet data, no paid data credentials, no broker integration, no real trading automation, and no personal production system state.

## What This Is

- A public Codex skill: `skills/apex-investment-strategy`
- A zero-pip Python toolkit using only the Python standard library and SQLite
- A local research workflow for price data, momentum signals, backtests, wallet drift, Action Packets, and static dashboard generation
- A starting point users can fork and adapt to their own data and constraints

## What This Is Not

- Not financial advice
- Not a managed portfolio service
- Not a trading bot
- Not connected to any broker API
- Not a copy of any private Apex production wallet, data warehouse, or automation setup
- Not a source of personalized buy/sell recommendations

## Requirements

- Python 3.10+
- Git
- Optional: Codex skill support if you want to install the skill into Codex

No pip install is required for the baseline workflow.

## Fastest Smoke Test

From a fresh clone:

```bash
git clone https://github.com/UltraDD/apex-investment-strategy.git
cd apex-investment-strategy
python -m unittest discover -s tests
```

The test suite runs the public workflow in a temporary directory: project initialization, sample database creation, data validation, research backtest, paper wallet, Action Packet, and static dashboard scaffold.

## Install The Codex Skill

You can run the scripts directly from this repository without installing the skill. Install the skill only if you want Codex to discover `apex-investment-strategy` as a reusable workflow.

From the repository root, copy the skill directory into your Codex skills folder.

macOS / Linux:

```bash
mkdir -p ~/.codex/skills
rm -rf ~/.codex/skills/apex-investment-strategy
cp -R skills/apex-investment-strategy ~/.codex/skills/
```

Windows PowerShell:

```powershell
$dest = Join-Path $env:USERPROFILE ".codex\skills\apex-investment-strategy"
Remove-Item -Recurse -Force $dest -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
Copy-Item -Recurse -Force ".\skills\apex-investment-strategy" $dest
```

Restart Codex after installation. Then you can ask:

```text
Use apex-investment-strategy to initialize a local research workspace in ./my-apex with sample data.
```

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

This creates a local research workspace with:

```text
demo-apex/
  config.json
  data/apex.sqlite
  reports/data-health.json
  reports/backtest-summary.json
  reports/signals.csv
  reports/latest-action.json
  wallet/transactions.example.csv
  web/index.html
```

The generated `demo-apex/` folder is ignored by git. It is for local experiments only.

## Minimum Working Example

If you only want the smallest end-to-end example, run these commands from the repository root:

```bash
python skills/apex-investment-strategy/scripts/init_project.py --project-dir ./demo-apex
python skills/apex-investment-strategy/scripts/init_database.py --project-dir ./demo-apex --sample
python skills/apex-investment-strategy/scripts/validate_data.py --project-dir ./demo-apex
python skills/apex-investment-strategy/scripts/run_backtest.py --project-dir ./demo-apex
python skills/apex-investment-strategy/scripts/build_action_packet.py --project-dir ./demo-apex
```

What to expect:

- `validate_data.py` should report enough sample history for the default assets.
- `run_backtest.py` writes `reports/backtest-summary.json` and `reports/signals.csv`.
- `build_action_packet.py` writes `reports/latest-action.json`.
- All outputs are marked research-only and use generated sample data unless you import your own CSV.

Sample results are smoke-test evidence only. Do not treat them as market evidence, live performance, or a trading signal.

## Apex-Aligned 17-Asset Track

The default quick start is intentionally small. If you want a workspace that is closer to the public shape of Apex, initialize with the 17-asset profile:

```bash
python skills/apex-investment-strategy/scripts/init_project.py --project-dir ./my-apex --profile apex17
python skills/apex-investment-strategy/scripts/init_database.py --project-dir ./my-apex --sample
python skills/apex-investment-strategy/scripts/validate_data.py --project-dir ./my-apex
```

The `apex17` profile scaffolds a public 17-asset universe and keeps the same runnable baseline. It does not ship live data, private production rules, paid credentials, broker integration, or personal wallet state.

For a guided migration from sample data toward a fuller Apex-like research setup, read `skills/apex-investment-strategy/references/apex-alignment-guide.md`.

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

## Use Your Own Data

Create a CSV with the schema above, then import it after initializing the project:

```bash
python skills/apex-investment-strategy/scripts/init_project.py --project-dir ./my-apex
python skills/apex-investment-strategy/scripts/init_database.py --project-dir ./my-apex --csv ./prices.csv
python skills/apex-investment-strategy/scripts/validate_data.py --project-dir ./my-apex
```

Keep your local price files, SQLite database, wallet files, and reports private unless you intentionally sanitize them.

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

## Public Boundary Checklist

Before publishing a fork or sharing generated output, check that you are not exposing:

- Real brokerage exports, order history, or account identifiers
- Real wallet state, position sizes, transaction logs, or portfolio screenshots
- Paid data credentials, API keys, `.env` files, cookies, or local token caches
- Private production strategy code, private market-data warehouses, or personal workspace paths
- Generated SQLite databases, reports, Action Packets, or dashboard files that include personal data

The repository `.gitignore` excludes generated `demo-apex/`, SQLite databases, local reports, wallet files, dashboard output, logs, and common secret files.

## Safety

Every generated output is research-only. Use your own judgment, consult qualified professionals for financial decisions, and verify data quality before relying on any signal.

See [DISCLAIMER.md](DISCLAIMER.md) for the full disclaimer.
