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
- **Comments:** Always wrap descriptive summaries containing numbers/units (e.g., "261 W") in double quotes (`" "`) at the top of the file.
- **Step Syntax:** Every executable workout step must start with a hyphen and a space `- `.
- **Order:** The order must be `[Hyphen] [Step Note (Optional)] [Duration] [Intensity]`. (e.g. `- Work 20m 90%` NOT `- 20m 90% Work`)
- **Loops:** Repetitions like `Nx` or `3x` must be on their own line with the repeated steps following underneath.
- **Targets:** Use `%` of FTP for all power targets — **never use zone names (Z1, Z2, Z4, etc.)**
- Do not include a cool-down step

### Template

```text
"Workout summary description with numbers like 261 W must be in quotes"

- Free spin 5m 52%
- Warm up 10m 63%

Nx
- Step note 1 xm xx%
- Step note 2 xm xx%
"Xg carbs within 10 min post-ride"
```

### Example — 3×20 min SST

```text
"3x20 at 90% FTP with 5 min recovery"

- Free spin 5m 52%
- Warm up 10m 63%

3x
- Work 20m 90%
- Recovery 5m 52%
"Xg carbs within 10 min post-ride"
```

### Example — 5×5 min VO2max

```text
"5x5 at 108% FTP"

- Free spin 5m 52%
- Warm up 10m 63%

5x
- Work 5m 108%
- Recovery 5m 52%
"Xg carbs within 10 min post-ride"
```

## Post-Ride Nutrition (Carb Replenishment)

At the end of every generated session plan, include a calculation of the post-ride carbohydrates the athlete should consume within 10 minutes.

Use the planned ride duration and estimated TSS/h to determine the multiplier (g/kg), then calculate the total grams based on the athlete's body weight (refer to the `cycling-athlete-profile` skill for current body weight). Estimate the total TSS based on the planned intensity/duration if not explicitly provided.

| Ride duration | TSS/h | Post-ride drink (within 10 min) |
|---------------|-------|---------------------------------|
| ≤45 min       | <50   | 0.3–0.4 g/kg                    |
| ≤45 min       | 50–60 | 0.4–0.5 g/kg                    |
| ≤45 min       | 61–72 | 0.5–0.6 g/kg                    |
| ≤45 min       | ≥73   | 0.5–0.7 g/kg                    |
| 46–75 min     | <50   | 0.3–0.4 g/kg                    |
| 46–75 min     | 50–60 | 0.4–0.5 g/kg                    |
| 46–75 min     | 61–72 | 0.5–0.6 g/kg                    |
| 46–75 min     | ≥73   | 0.6–0.7 g/kg                    |
| 76–120 min    | <50   | 0.4–0.5 g/kg                    |
| 76–120 min    | 50–60 | 0.5–0.6 g/kg                    |
| 76–120 min    | 61–72 | 0.6–0.7 g/kg                    |
| 76–120 min    | ≥73   | 0.7–0.8 g/kg                    |
| 121–180 min   | <50   | 0.8–0.9 g/kg                    |
| 121–180 min   | 50–60 | 0.9–1.0 g/kg                    |
| 121–180 min   | 61–72 | 1.0–1.1 g/kg                    |
| 121–180 min   | ≥73   | 1.1–1.2 g/kg                    |
| 181–240 min   | <50   | 0.8–0.9 g/kg                    |
| 181–240 min   | 50–60 | 1.0–1.1 g/kg                    |
| 181–240 min   | 61–72 | 1.1–1.2 g/kg                    |
| 181–240 min   | ≥73   | 1.2 g/kg                        |
| >240 min      | <50   | 0.8–0.9 g/kg                    |
| >240 min      | 50–60 | 1.0–1.1 g/kg                    |
| >240 min      | 61–72 | 1.1–1.2 g/kg                    |
| >240 min      | ≥73   | 1.2 g/kg                        |

**Format Example:**
`Post-ride carbs (within 10 min): 0.5–0.6 g/kg = 38–46g`
