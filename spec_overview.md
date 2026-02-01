# Sleep Log Web App Specification (MVP)

## Goal
Replace daily handwritten ledgers with a smartphone-friendly web application that:
- collects daily sleep/wake records via forms (no manual date typing),
- stores data in the cloud with user login (privacy),
- exports submission-ready PDFs that match the existing paper layout using a template-background method,
- supports monthly reports and weekly (arbitrary range) reports,
- when the selected range spans multiple months, outputs ZIP (recommended) + per-month PDF downloads (fallback).

## Key Decisions (Fixed)
- Platform: Responsive Web App (cloud-hosted). Optional PWA later.
- Authentication: Email + Password (with password reset).
- Storage: Cloud DB (per-user isolation).
- PDF: No persistent PDF storage. Generate on demand and immediately download.
- PDF Layout: Paper-identical layout using template image as background + coordinate-based drawing.
- Reports: Monthly + Range (weekly). For range spanning months: split per month.
- Date Input: No manual typing. Use calendar selection (default) and wheel (year/month/day) as auxiliary.

## Scope (MVP)
Included:
- Login / Signup / Password reset
- Home (today quick entry)
- Calendar (monthly view + day status)
- Daily entry (form-first, timeline view optional)
- PDF export (month/range), ZIP + per-month fallback
- Settings (name/ID for PDF header, timezone, logout)
- Developer tools: template calibration + debug PDF overlay

Excluded (Post-MVP):
- Full drag-edit timeline UI (can be view-only first)
- 2FA/passkeys (optional later)

## Target Users / Use Case
Individuals required to submit a Sleep/Wake Rhythm Table to medical providers.

## Terminology
- In-bed period: time in bed (bedtime -> out-of-bed), drawn as a band/arrow.
- Sleep segments: multiple intervals classified as:
  - deep sleep (ぐっすり) = filled black
  - doze (うとうと) = hatched
  - awake in bed (眠れないまま) = outline only
- Events: point markers
  - sleep medication (▲), toilet (▽), other meds (○/● etc)
- Sleepiness: morning rating 1–10.
- Night toilet count: integer (>=0), time points optional.

## Non-Functional Requirements
- Mobile-first UI (iPhone primary).
- Privacy: TLS, per-user access control, minimal logging.
- PDF fidelity: server-side generation recommended to avoid client font/rendering variance.
