# Screen Specifications (MVP)

## Global Navigation (Bottom Tabs)
- Home
- Calendar
- PDF Export
- Settings

Pre-login:
- Login / Signup / Password Reset only

---

## 1) Login
Inputs:
- Email
- Password
Actions:
- Login
- Signup link
- Forgot password link

Validation:
- Email format
- Password not empty

Errors:
- Invalid credentials
- Network/server error

---

## 2) Signup
Inputs:
- Email
- Password (>= 8 chars)
- Password confirmation
On success:
- Redirect to Settings/Profile (name/ID required for PDF header)

---

## 3) Password Reset
- Email input -> send reset email
- Completion message

---

## 4) Home
Purpose: fastest path to today entry
- Today date (YYYY/MM/DD + weekday)
- Status: Not started / Incomplete / Complete
- Primary button: Enter Today
- Quick summary:
  - Sleepiness
  - Night toilet count
  - In-bed time range
  - Number of segments (deep/doze/awake-in-bed)

Secondary:
- Enter Yesterday
- Go to Calendar

---

## 5) Calendar (Monthly)
Purpose: eliminate date manual input
- Month navigation (buttons + swipe)
- Today shortcut
- Day cells show status:
  - complete: ✅
  - incomplete (required missing): ⚠️
  - no input: ⬜
- Tap day -> Daily Entry

Aux: Wheel date picker
- Modal: year/month/day wheels
- OK/Cancel
- Day range auto-adjusts (month/leap year)

---

## 6) Daily Entry (Core)
Header (sticky):
- Date (YYYY/MM/DD + weekday)
- Prev/Next day
- Tap date -> Calendar (default) or wheel picker
- Save status: unsaved/saved

Required block:
1) Morning Sleepiness (1–10, integer)
2) Night Toilet Count (>=0, integer)
   - Optional: add toilet time events if known

In-bed period (basically required):
- Bedtime (start)
- Out-of-bed (end)
- Toggle: out-of-bed unknown
Cross-midnight supported.

Sleep window (basically required):
- Sleep start
- Sleep end
- Toggles: start unknown / end unknown
Cross-midnight supported.

Sleep segments (multiple, overlap forbidden):
- Auto-sorted list
- Each: state, start/end, split/duplicate/delete
Helpers:
- Create from Sleep Window (deep one segment)
- Create from In-bed (deep one segment)

Events:
- Sleep medication (▲): time required, name optional
- Other meds: name required, time required, marker style selectable (○/●…)
- Toilet time (▽): optional time points

Notes:
- Multi-line, may truncate in PDF (warn)

Timeline accordion:
- MVP can be view-only

Save:
- Bottom fixed Save button
- Show aggregated errors/warnings at top; scroll to first issue

---

## 7) PDF Export
Modes:
- Monthly: year/month selection (no typing)
- Range (weekly): start–end (calendar range)

Pre-check summary (n/m/k):
- Period S–E
- n: days with any input
- m: no-input days (blank in PDF)
- k: days with missing required fields
- Link: Review missing days -> Calendar filter mode

Generate:
- Single-month -> download PDF
- Cross-month:
  - Primary: download ZIP (recommended)
  - Fallback: download each month PDF

iPhone guide:
- Files -> Downloads -> tap ZIP to unzip
- For submission, per-month PDF may be easier.

---

## 8) Settings
- Profile: Name, ID, Timezone (default JST)
- Logout
- Optional: default helper toggle (auto-create segments)
