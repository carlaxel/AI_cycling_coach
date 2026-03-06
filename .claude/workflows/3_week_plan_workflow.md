# 3-Week Workout Plan Generation Workflow

This workflow defines the standard operating procedure for generating a 3-week cycling training block for the athlete, ensuring adherence to their profile, schedule, and formatting requirements.

## 1. Pre-Flight Checks & Inputs
Before generating a plan, verify the current state using the `cycling-athlete-profile`:
- **Current Phase:** (e.g., Q1 Indoor Base Building, Threshold Build, VO2max).
- **Current FTP:** 290 W (Working FTP for 2026).
- **Target Volume:** 7–10 hours per week.
- **Meso-cycle Structure:** 3 Weeks Build + 1 Week Recovery (volume reduced by 30-40%, keeping one intensity session). This directly addresses the 2025 lesson of missing systematic recovery weeks.

## 2. Weekly Schedule Template
Follow the athlete's work/life schedule constraints, ask to verify any changes, and generate the plan accordingly. If summer then more days might be available for longer rides mid week, but if winter then the schedule is more constrained. Possible template, but adjust intensity and volume based on the current phase and target progression:
- **Monday (WFH):** Structured Intensity (e.g., SST / Threshold).
- **Tuesday (Office):** Rest or Active Recovery (< 55% FTP).
- **Wednesday (WFH):** Structured Intensity (e.g., SST / Threshold).
- **Thursday (Office):** Rest or Active Recovery (< 55% FTP).
- **Friday (WFH):** Structured Intensity or Long Endurance.
- **Saturday:** Long Endurance (Z2: 56–75% FTP).
- **Sunday:** Recovery / Easy Z2 (Always easy post-date night).

## 3. Session Formatting Requirements
Every generated session must strictly follow the `session-creation` skill rules:
1. **Warm-up:** 
   - Endurance: Max 5 min.
   - Structured: 5 min @ 52% FTP + 10 min @ 63% FTP.
2. **Main Set:** Progress the time-in-zone across the build weeks. Use `%` of FTP for all power targets (e.g., `90%`, not `Z4`).
3. **No Cool-down:** Do not include a planned cool-down block in the structure.
4. **intervals.icu Block:** Include the copy-paste ready text block for direct import.
5. **Nutrition:** Append the post-ride carbohydrate calculation based on ride duration and expected TSS.

## 4. Execution Steps

When asked to generate a 3-week plan, the AI should execute the following sequence:

### Step 1: Design the Progression
**Delegate this step to the `cycling-coach` subagent.** It must define the primary progression target for the block (e.g., extending SST time-in-zone from 3x15m to 2x30m). Ensure the week after the 3rd week is a clear recovery week.

### Step 2: Draft the Block Plan
Create a high-level overview document (e.g., `workout_plans/plan_[Phase]_[Date].md`) detailing the daily volume, target TSS, and session goals across the 21 days.

### Step 3: Generate the intervals.icu Blocks
Embed the workout text blocks directly into the plan document for every structured session.

**Template Reference:**
```text
"Workout summary description with numbers like 261 W must be in quotes"

- Free spin 5m 52%
- Warm up 10m 63%

Nx
- Work xm xx%
- Recovery xm xx%
```

**Post-Ride Nutrition Example:**
`Post-ride carbs (within 10 min): 0.5–0.6 g/kg = 48–57g`

### Step 4: Review Against Athlete Flaws
Ensure the plan does not repeat 2025 mistakes:
- Is the FTP ceiling being respected? (No VO2max during early base).
- Is the recovery week actually a recovery week?
- Are the weekend rides aligned with the athlete's pure diesel physiology?
