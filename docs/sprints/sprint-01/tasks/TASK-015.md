# TASK-015: Mobile-first responsive app shell layout

- **Backlog item:** BL-005
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-012, TASK-014
- **Estimate:** S

## Description
Make the shell usable on phone-size screens (BL-005 AC3).

## Technical Notes
- Shared `AppShell` layout: header (title, language switcher), content area, bottom navigation placeholder for the active area. Viewport meta, safe-area insets, touch targets >= 44px, readable at 360px width, no horizontal scroll.
- Works in both RTL and LTR. Semantic HTML, labelled controls, keyboard navigation.

## Acceptance Criteria
- [x] At 360x640 and 1280x800 viewports in both languages there is no overflow or broken layout
- [x] Accessibility basics: labels, focus visible, landmarks
- [x] Tests written and passing; lint clean

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — frontend: Added AppShell (skip link, header with title + language switcher, single <main>, labelled bottom nav with active area), safe-area insets (viewport-fit=cover), 44px touch targets, focus-visible, logical CSS only. Fixed a regression: the Noto Sans Arabic font was missing from the font stack after earlier formatting (now present, tested). 43 tests passing, lint clean, build OK. Verified in headless Chrome on the production build at 360x640 and 1280x800, en and ar, on /, /driver, /admin, /nope: no horizontal overflow, dir correct, all links/buttons >= 44px, bottom nav text fits; checked a 360px Arabic screenshot. Not tested: real devices, screen reader. Status IN_REVIEW.
- 2026-10-10 — qa: TASK-022 frontend QA PASS (QA_REPORT.md; 30/30 real-browser cases, 47 unit tests); status DONE.
