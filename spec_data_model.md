# Data Model (Logical)

## User
- id
- email
- display_name (for PDF header)
- sheet_id (for PDF header)
- timezone (default JST)
- created_at, updated_at

## DayLog (1 per user per date)
- id
- user_id (FK)
- date (YYYY-MM-DD)
- sleepiness_rating (int 1..10, nullable)
- night_toilet_count (int >=0, nullable)
- notes_text (string, nullable)
- created_at, updated_at

Derived (can be computed):
- completion_status: complete / incomplete_required_missing

## InBedPeriod (0..1 per DayLog)
- id
- day_log_id (FK)
- start_datetime (nullable)
- end_datetime (nullable)
- end_unknown (bool)

## SleepWindow (0..1 per DayLog)
- id
- day_log_id (FK)
- start_datetime (nullable)
- end_datetime (nullable)
- start_unknown (bool)
- end_unknown (bool)

## SleepSegment (0..N per DayLog)
- id
- day_log_id (FK)
- start_datetime
- end_datetime
- state: deep_sleep | doze | awake_in_bed
- source: manual | auto_generated
Constraint:
- Non-overlap among segments per day_log_id

## Event (0..N per DayLog)
- id
- day_log_id (FK)
- type: sleep_med | toilet | other_med
- datetime (nullable for toilet if time unknown; meds should be non-null)
- label (drug name etc)
- marker_style (for other_med: circle/filled etc)

Indexes (recommended):
- unique(user_id, date)
- segments(day_log_id, start_datetime)
- events(day_log_id, datetime)
