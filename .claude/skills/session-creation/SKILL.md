---
name: session-creation
description: Athlete preferences and formatting rules for creating cycling session plans. Use when building workout plans, writing intervals.icu blocks, or structuring any training session for this athlete.
---

# Session Creation Guidelines

## intervals.icu Integration

The athlete has an intervals.icu account. Credentials are in `.claude/memory/MEMORY.md` (gitignored).
- **API base URL:** `https://intervals.icu/api/v1`
- **Auth:** HTTP Basic — username literal `API_KEY`, password = key from MEMORY.md
- **Athlete ID:** `i129467`. Use `i129467` explicitly (not `0`) in practice.

### Pushing a workout to the calendar

Use `POST /api/v1/athlete/i129467/events` — this places the workout **directly on the schedule**.
Do NOT use `/workouts` (that goes to the library folder, not the calendar).

Send a JSON body with a ZWO file embedded as `file_contents`:

```bash
curl -X POST \
  -u "API_KEY:<key>" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "WORKOUT",
    "start_date_local": "YYYY-MM-DDT00:00:00",
    "type": "VirtualRide",
    "name": "Session name",
    "description": "Short description",
    "filename": "session.zwo",
    "file_contents": "<ZWO XML here>"
  }' \
  "https://intervals.icu/api/v1/athlete/i129467/events"
```

### ZWO format

Use `SteadyState` elements with `Duration` (seconds) and `Power` (fraction of FTP, e.g. `0.90` = 90%).

**IMPORTANT: Do NOT use `<Repeat>` — it is not parsed correctly by the API. Always expand repeats into individual `SteadyState` elements.**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<workout_file>
  <author>Carl-Axel Hallgren</author>
  <name>SST 2x20 @ 90% FTP</name>
  <description>...</description>
  <sport_type>bike</sport_type>
  <workout>
    <SteadyState Duration="300" Power="0.52"/>   <!-- 5m free spin -->
    <SteadyState Duration="600" Power="0.63"/>   <!-- 10m warm-up -->
    <SteadyState Duration="1200" Power="0.90"/>  <!-- 20m @ 90% -->
    <SteadyState Duration="300" Power="0.52"/>   <!-- 5m recovery -->
    <SteadyState Duration="1200" Power="0.90"/>  <!-- 20m @ 90% -->
    <SteadyState Duration="300" Power="0.52"/>   <!-- 5m recovery -->
    <SteadyState Duration="1500" Power="0.63"/>  <!-- 25m endurance -->
  </workout>
</workout_file>
```

### Verify upload

Check `moving_time` in the response equals the expected total seconds (e.g. 90 min = 5400 s).
If wrong, the steps were not parsed — delete and re-upload with corrected XML.

```bash
# Delete an event
curl -X DELETE -u "API_KEY:<key>" \
  "https://intervals.icu/api/v1/athlete/i129467/events/<id>"
```

## Weekly Schedule Context

Use this when planning which days to schedule hard vs easy sessions:

| Day       | Context                                      | Training implication                        |
|-----------|----------------------------------------------|---------------------------------------------|
| Monday    | Work from home                               | Flexible — good for structured sessions     |
| Tuesday   | Office day                                   | Less flexible — prefer easier or rest       |
| Wednesday | Work from home                               | Flexible — good for structured sessions     |
| Thursday  | Office day                                   | Less flexible — prefer easier or rest       |
| Friday    | Work from home                               | Flexible — good for longer or harder work   |
| Saturday  | Date night (alcohol likely)                  | Can train in the morning; evening is social |
| Sunday    | Post date-night recovery                     | **Always easy** — low-intensity or rest     |

Default hard-day slots: **Monday, Wednesday, Friday** (home days).
Default easy/rest slots: **Tuesday, Thursday** (office days), **Sunday** (recovery).

## Warm-up

- **Endurance sessions:** Max 5 min planned warm-up.
- **Interval / structured sessions:** 5 min free spin at 50–55%, then minimum 10 min at 60–65% before the main set.

## Cool-down

No planned cool-down — athlete will do unstructured spinning if needed. **Do not include cool-down blocks in session plans.**

## File Location

Save all workout plan files to the `workout_plans/` directory in the project root.

## Workout Format

All structured sessions must include an **intervals.icu workout builder block** — plain text, copy-paste ready for direct import.

Rules:
- Use `%` of FTP for all power targets — **never use zone names (Z1, Z2, Z4, etc.)**
- Use `Nx` repeat syntax for intervals
- Do not include a cool-down step

### Template

```
Free spin
- 5m 52%

Warm up
- 10m 63%

Main set Nx
- Xm XX%
- Xm XX%
```

### Example — 3×20 min SST

```
Free spin
- 5m 52%

Warm up
- 10m 63%

Main set 3x
- 20m 90%
- 5m 52%
```

### Example — 5×5 min VO2max

```
Free spin
- 5m 52%

Warm up
- 10m 63%

Main set 5x
- 5m 108%
- 5m 52%
```
