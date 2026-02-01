# API Specification (MVP)

All endpoints require authentication unless noted.

## 1) Logs Summary (for PDF pre-check + calendar filters)
POST /logs/summary
Body:
{
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD"
}
Response:
{
  "period": {"start_date":"...", "end_date":"..."},
  "n": 0,
  "m": 0,
  "k": 0,
  "missing_days": [
    {"date":"YYYY-MM-DD", "missing_fields":["missing_sleepiness", "..."]}
  ],
  "no_input_days": ["YYYY-MM-DD"],
  "complete_days": ["YYYY-MM-DD"]
}

## 2) DayLog CRUD
GET /logs/day?date=YYYY-MM-DD
POST /logs/day
PUT /logs/day/:id

Recommended response additions:
- completion_status
- missing_fields (if incomplete)
- warnings_fields (optional)

## 3) PDF Generation (no storage)
POST /pdf/generate
Body (monthly):
{ "mode":"month", "year":2026, "month":2, "debug":false }

Body (range):
{ "mode":"range", "start_date":"YYYY-MM-DD", "end_date":"YYYY-MM-DD", "debug":false }

Behavior:
- single month -> application/pdf attachment
- cross-month -> application/zip attachment (PDFs in root)

Per-month fallback:
- client calls same endpoint with month-contained ranges.

## 4) Month calendar status (optional)
GET /logs/month?year=2026&month=2
Response:
{ "days":[ {"date":"YYYY-MM-DD","status":"complete|incomplete|none"} ] }

## Error handling
- 400: validation errors (keys + messages)
- 401: unauthorized
- 403: forbidden
