---
name: session-matching
description: Rules for fingerprinting workouts and comparing repeated formats to track progression and detect FTP staleness. Fits perfectly into Phase 1 (Block Context) and Phase 4 (Historical Block Comparison).
---

# Session Matching & Progression Analysis

## 1. Goal
Provide rules for comparing repeated workout formats — fingerprinting workouts, tracking improvements in specific interval formats, and detecting FTP staleness from repeated session data.

## 2. Fingerprinting & Identifying Matches
A session is considered a match if it shares a core structural signature. 
To identify matching sessions, look for the following in historical session files:
- **Interval Structure:** The number of work intervals and their duration (e.g., 2×20m, 4×8m, 5×3m).
- **Target Intensity:** The target %FTP or Power range of the work intervals.
- **For Quality Sessions (VO2Max, Threshold, SST):** Matching MUST focus exclusively on the work intervals. Ignore variations in warm-up, cool-down, or rest intervals unless they drastically change the nature of the workout.
- **For Endurance (Z2):** Matching should be based on total duration (e.g., ±15 minutes) and target power range.

*Directive: When asked to find matches in Phase 1, find up to the 3 most recent matching sessions, even if they occurred outside the current 3-week block.*

## 3. Comparison Metrics & Progression Tracking
Once matches are found, compare the following metrics to evaluate physiological adaptation:
- **Power Output:** Did the athlete achieve a higher average or normalized power for the same duration?
- **Heart Rate Response:** For the same power output, was the average HR or peak HR lower?
- **Interval Decoupling (Pw:HR) / Efficiency Factor (EF):** Did EF increase? Did decoupling decrease (showing improved durability)?
- **Fade Index:** Was the athlete able to maintain power more consistently across all intervals compared to previous attempts?
- **RPE / Subjective Feel:** (If available) Did the session feel easier for the same output?

## 4. Detecting FTP Staleness
A key benefit of session matching is identifying when an athlete's physiological fitness has outgrown their currently set FTP.
Flag **FTP Staleness** if you observe a persistent pattern across recent matched quality sessions where:
- The athlete consistently overshoots the target power for the work intervals (e.g., target was 90% FTP, actual was 95% FTP).
- The physiological cost (HR, Decoupling, Fade) is lower than expected or improves despite the power overshoot.
- The athlete reports lower-than-expected RPE for the prescribed intensity.

**Action Plan for FTP Staleness:**
- **Frequency Limit:** Do not suggest FTP tests or direct FTP changes more often than once every 8 weeks.
- **Direct Increase:** If the historical data is overwhelmingly clear and consistent across multiple matched sessions, you may recommend directly increasing the FTP without a test.
- **Suggesting a Test:** If the data suggests a change but you are not completely certain, suggest an FTP test or schedule one to be added to the next generated training block.