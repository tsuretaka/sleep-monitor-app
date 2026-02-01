# Save-time Errors/Warnings + PDF Pre-check Rules

## A) Save-time Validation

Common UI behavior:
- On Save, show aggregated banner at top:
  - Errors (red): save blocked
  - Required-missing: save allowed, calendar shows ⚠️
  - Warnings (yellow): save allowed
- Auto-scroll to first item and highlight.

### Errors (Save Blocked)
E1 Overlapping sleep segments
- Condition: any overlap among segments.
- Message: 睡眠区間が重なっています。重なりを解消してください。

E2 Invalid segment duration
- Condition: start == end OR >= 24h (after cross-midnight split).
- Message: 開始と終了の時刻を確認してください。

E3 Time format invalid (rare)
- Message: 時刻の形式が不正です。選択し直してください。

### Required Missing (Save Allowed; status=⚠️)
R1 Sleepiness missing
- 眠気（1〜10）が未入力です。

R2 Night toilet count missing
- 夜間トイレ回数が未入力です。

R3 In-bed start missing
- 就床時刻が未入力です。

R4 In-bed end missing (end_unknown OFF)
- 離床時刻が未入力です（離床不明を選ぶこともできます）。

R5 Sleep start missing (start_unknown OFF)
- 入眠時刻が未入力です（入眠不明を選ぶこともできます）。

R6 Sleep end missing (end_unknown OFF)
- 覚醒時刻が未入力です（覚醒不明を選ぶこともできます）。

R7 Segments missing (with rescue)
- 睡眠区間が未入力です（睡眠時間から自動作成もできます）。

Rescue rule (segments):
- If segments == 0 AND sleep_start & sleep_end are available (or allowed by unknown toggles):
  - PDF generation auto-creates a single deep segment from sleep_start to sleep_end.
  - Do not count as required-missing (optional: show warning on export screen).

### Warnings (Save Allowed)
W1 Segments outside in-bed
- 睡眠区間が寝床滞在の範囲外です。必要に応じて調整してください。

W2 Segments outside sleep window
- 睡眠区間が睡眠時間の範囲外です。

W3 Sleep window longer than in-bed
- 睡眠時間が寝床滞在より長くなっています。入力を確認してください。

W4 Notes may be truncated
- 特記事項が長いため、PDFでは末尾が省略される可能性があります。

Optional save confirmation (when required missing exists):
- Title: 必須項目が未入力です
- Body: このまま保存すると「一部不足」として記録されます。後で修正できます。
- Buttons: 不足を修正する / このまま保存

---

## B) PDF Export Pre-check (n/m/k)

Definitions:
- Period: S..E inclusive, D = all dates in period
- n = count(has_any_input(d)=true)
- m = |D| - n
- k = count(has_any_input(d)=true AND has_required_missing(d)=true)

has_any_input(d) is true if any exists:
- sleepiness set
- toilet count set (including 0)
- in-bed start/end or unknown toggle set
- sleep start/end or unknown toggle set
- segments >= 1
- events >= 1
- notes length >= 1

Output behavior:
- If n==0: allow generation with confirmation (blank PDF ok?).
- If k>0: allow generation, show warning and link to missing-day review.
- Cross-month: show total n/m/k; optional per-month breakdown.
