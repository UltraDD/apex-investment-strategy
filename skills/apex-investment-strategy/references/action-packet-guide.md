# Action Packet Guide

An Action Packet is a local report that explains the current strategy target, data health, wallet drift, and possible paper trades.

Generate it with:

```bash
python scripts/build_action_packet.py --project-dir ./my-apex
```

Output:

- `reports/latest-action.json`

## Contents

| Field | Meaning |
|---|---|
| `status` | `research_only` or a validation warning |
| `signal_date` | Latest date used by the signal |
| `target_weights` | Strategy target weights |
| `portfolio` | Paper wallet value estimate |
| `recommended_trades` | Local target-drift table |
| `data_health` | Coverage summary |
| `disclaimer` | Research-only safety text |

## Interpretation Rule

The Action Packet is not an instruction. It is a local evidence bundle. The user remains responsible for checking data, costs, taxes, liquidity, and suitability.

Do not hide warnings. If data coverage is short, say so before discussing target weights.

