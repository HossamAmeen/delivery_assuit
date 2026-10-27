# TASK-009: Backend i18n: Arabic/English server messages

- **Backlog item:** BL-006
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-003
- **Estimate:** S

## Description
Server error/success messages must be available in Arabic and English (BL-006 AC4). Backend half of the bilingual requirement.

## Technical Notes
- Enable `LocaleMiddleware`, `LANGUAGES = [('ar','Arabic'),('en','English')]`, `LOCALE_PATHS`, default `en`. Language chosen from the `Accept-Language` header.
- Wrap all `common/` messages (validation fallback, auth, permission, not found, throttled, server error, health) in `gettext_lazy`; provide `locale/ar/LC_MESSAGES/django.po` and compiled `.mo` via `make compilemessages`.
- Add a rule to the backend README: every new user-facing message uses gettext.
- Update API_CONTRACT.md with the Accept-Language behavior if details changed.

## Acceptance Criteria
- [x] Same error request returns Arabic message with `Accept-Language: ar` and English with `en` or none
- [x] 401, 403, 404, 429 and validation-failed messages all translated
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — backend: Wrapped all server messages (exception handler, envelope default, health, auth, ApplicationError defaults) in gettext_lazy; LOCALE_PATHS=backend/locale; locale/ar django.po + compiled .mo; make compilemessages (msgfmt or scripts/compile_messages.py fallback since gettext is not installed here); README rule added. 9 new tests; full suite 97 passing, ruff clean. API_CONTRACT unchanged (Accept-Language behavior already matched). Status IN_REVIEW.
- 2026-10-10 — qa: TASK-021 backend QA PASS (see QA_REPORT.md); status DONE.
