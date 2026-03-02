⏺ Here's a consolidated review of the code and reports, prioritized by
   impact:

  ---
  HIGH — Bugs

  1. Session type mislabeling (reporter.py)
  Sessions with IF 0.60–0.80 are being labeled "Recovery" instead of
  "Endurance". This cascades into false TSS warnings ("TSS 50 is high
  for a Recovery session" when 50 is perfectly normal for Endurance).
  Affects at least 5 sessions across W07–W09. The CLAUDE.md thresholds
   are clear: Recovery < 0.60, Endurance 0.60–0.80.

  2. Null check missing for target_power_high (reporter.py:523)
  Lap compliance display checks target_power_low is not None but uses
  target_power_high without guarding — could render "243–None W" for
  FIT files with partial target data.

  ---
  HIGH — Missing Features

  3. W/kg not surfaced anywhere
  The athlete profile emphasizes W/kg (3.1 W/kg at 95 kg), but no
  rider weight is captured in models, no W/kg calculation in analyzer,
   and reports never show relative power. This is the most meaningful
  metric for tracking progress.

  4. Pedaling dynamics underutilized in insights
  Session reports surface L/R balance, torque effectiveness, and pedal
   smoothness beautifully. But the weekly summary and critique don't
  analyze trends — e.g., "L/R asymmetry worsened through intervals" or
   "torque effectiveness dropped in final 20 minutes (fatigue
  marker)".

  ---
  MEDIUM — Code Quality

  5. Duplicated formatting utilities
  _fmt_duration(), _fmt_dist(), _fmt_speed(), and _bar() are
  copy-pasted between formatter.py and reporter.py (with _bar() using
  different widths: 30 vs 20). Fix one, forget the other.

  6. Inconsistent duration logic
  formatter.py uses timer_time or elapsed_time, session reports use
  timer_time only, weekly table uses timer_time or elapsed_time. A
  session could show "—" in one place and "45m" in another.

  7. Private functions used as public API
  report.py imports _session_filename() and _week_label() from
  reporter.py — these should be public (drop the underscore) since
  they're part of the external interface.

  ---
  MEDIUM — Report Quality

  8. TSS trend detection too strict (reporter.py:903)
  Block analysis requires strict monotonic increase (all(tss[i] <
  tss[i+1])) to detect "progressive loading". A week that dips 2 TSS
  then resumes climbing fails detection. Should use a trend line or
  tolerance.

  9. VI = 1.0 misinterpreted on trainer sessions
  Commentary praises VI < 1.010 as "excellent pacing," but on indoor
  trainers constant power is the default mode — it's not a pacing
  skill indicator. Should note this for sub_sport = 'indoor_cycling'.

  10. No workout name/intent captured from FIT
  FIT files contain workout names ("Sweet Spot 3×8min") and user notes
   from Garmin Connect, but the parser ignores them. This means
  reports can't reference training intent.

  ---
  LOW — Nice-to-haves

  11. Weekly summary doesn't aggregate total elevation gain
  12. Temperature trends not analyzed (useful for HR drift context)
  13. Indoor/outdoor session mixing not flagged in weekly comparisons
  14. _v() format string pattern is fragile — '{:.0f}' works but
  breaks if helper is refactored
  15. No graceful handling when FIT laps don't match workout steps
  (silent wrong pairing)