# Developer Tools: Calibration & Debug PDF

## Calibration UI (/admin/calibrate)
Clicks (minimum 12):
1) time_grid_left_x
2) time_grid_right_x
3) day_grid_top_y
4) day_grid_bottom_y
5) sleepiness_col_left_x
6) sleepiness_col_right_x
7) notes_col_left_x
8) notes_col_right_x
9) header_id_anchor
10) header_name_anchor
11) header_year_anchor
12) header_month_anchor

Store normalized coordinates.

Overlay & self-check:
- draw the captured lines
- compute row_height
- optional noon midpoint check
- warn if mismatches exceed tolerance

## Debug PDF Mode
pdf/generate supports debug=true:
- draw grid boundaries (time/day/columns)
- draw time markers at 0/6/12/18/24 with x labels
- label D=1/D=31 with y labels
- label each segment with state + time + coords
- label each marker with type + time + coords

Cross-month + debug=true:
- generate debug PDFs per month and bundle into ZIP

## Golden Test Data (recommended)
1) 23:00–06:00 split
2) deep->doze->deep
3) in-bed larger than sleep window
4) toilet count only + sleepiness
5) long notes wrap/truncate
