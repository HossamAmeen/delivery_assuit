# TASK-012: Frontend i18n: Arabic/English, RTL/LTR layout, language switcher

- **Backlog item:** BL-006
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-010
- **Estimate:** M

## Description
Make the whole shell bilingual with correct direction (BL-006 AC1-3).

## Technical Notes
- `vue-i18n` (Composition API) with `src/locales/{en,ar}.json`; no hard-coded user-facing strings in components (including placeholder layouts, 404, health widget).
- Language store (Pinia) sets `document.documentElement.lang` and `dir` (`rtl` for ar, `ltr` for en); choice persisted in `localStorage` (guard with try/catch) defaulting to `en` (PO decision 2026-10-08); user can switch to `ar`.
- Language switcher component in the shared header. Use CSS logical properties (`margin-inline-start`, `inset-inline`, etc.) so layouts mirror correctly; no left/right hard-coding.
- Choose an Arabic-capable font stack (self-hosted, no CDN dependency for PWA offline use).

## Acceptance Criteria
- [x] Switching language flips text and layout direction on every existing screen without reload
- [x] Choice survives page refresh
- [x] Adding a new locale key requires touching only the locale files
- [x] Vitest tests for store (dir/lang set, persistence) and switcher; lint clean
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — frontend: Added vue-i18n (en/ar JSON), language Pinia store (lang/dir on <html>, localStorage with try/catch, default en), LanguageSwitcher in a shared AppHeader (App.vue), all strings moved to locale files, CSS logical properties, self-hosted Noto Sans Arabic via @fontsource. 27 tests passing, lint clean, build OK. Not verified visually in a browser. Status IN_REVIEW.
- 2026-10-10 — qa: TASK-022 frontend QA PASS (QA_REPORT.md; 30/30 real-browser cases, 47 unit tests); status DONE.
