---
name: session-creation
description: Athlete preferences and formatting rules for creating cycling session plans. Use when building workout plans, writing intervals.icu blocks, or structuring any training session for this athlete.
---

# Session Creation Guidelines

## Warm-up

- **Z2 sessions:** Max 5 min planned warm-up.
- **Interval / structured sessions:** 5 min free spin (Z1), then minimum 10 min Z2 before the main set.

## Cool-down

No planned cool-down — athlete will do unstructured spinning if needed. **Do not include cool-down blocks in session plans.**

## Workout Format

All structured sessions must include an **intervals.icu workout builder block** — plain text, copy-paste ready for direct import.

Rules:
- Use `%` of FTP for power targets (not absolute watts)
- Use zone names (`Z2`, `Z4`) where the effort is zone-wide rather than a precise %
- Use `Nx` repeat syntax for intervals
- Do not include a cool-down step

### Template

```
Free spin
- 5m Z1

Warm up
- 10m Z2

Main set Nx
- Xm XX%
- Xm XX%
```

### Example — 3×20 min SST

```
Free spin
- 5m Z1

Warm up
- 10m Z2

Main set 3x
- 20m 90%
- 5m 53%
```

### Example — 5×5 min VO2max

```
Free spin
- 5m Z1

Warm up
- 10m Z2

Main set 5x
- 5m 108%
- 5m 53%
```
