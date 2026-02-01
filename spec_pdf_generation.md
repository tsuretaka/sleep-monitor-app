# PDF Generation Specification (Template Background)

## Output Types
- Monthly PDF: one month (1–31 rows; unused rows blank)
- Range PDF: arbitrary range; if spans months, split per month
- Cross-month: provide ZIP (recommended) + per-month PDFs (fallback)

## Layout Strategy
- Use blank paper template image as background (A4 portrait)
- Draw user data on top using coordinates
- Server-side generation recommended

## Coordinate System
Store calibration points as normalized (0..1) relative to template image.

Minimum calibration params:
- time_grid_left_x, time_grid_right_x
- day_grid_top_y, day_grid_bottom_y
- sleepiness_col_left_x, sleepiness_col_right_x
- notes_col_left_x, notes_col_right_x
- header anchors: id/name/year/month text start (x,y)

Derived:
- row_height = (day_grid_bottom_y - day_grid_top_y) / 31
- time_grid_width = time_grid_right_x - time_grid_left_x

## Mapping
Day row:
- day_index = 1..31
- row_top_y = day_grid_top_y + (day_index-1)*row_height

Time to X:
- x = time_grid_left_x + (minutes_from_0/1440)*time_grid_width

Cross-midnight split:
- Split intervals into [start, 24:00) and [00:00, end) on next day row.

## Z-order
1) template background
2) in-bed band
3) sleep segments
4) point events
5) text (sleepiness, notes, headers)

## Styles
- deep sleep: filled black rectangle
- doze: hatched rectangle
- awake in bed: outline rectangle
- in-bed: light band + double arrow line
- markers: ▲ (sleep med), ▽ (toilet), ○/● (other meds)

Row vertical placement:
- y = row_top + row_height*0.15
- h = row_height*0.70

## Right Columns
Sleepiness:
- centered in sleepiness column
Notes:
- wrap in notes column; truncate with "…" if too long

## File Naming
PDF:
- sleep_log_{YYYY-MM}_{START}-{END}.pdf  (START/END in YYYYMMDD)
ZIP:
- sleep_log_{START}-{END}.zip (PDFs in root, no subfolders)

## No Storage
- Stream as attachment; do not persist PDFs.
