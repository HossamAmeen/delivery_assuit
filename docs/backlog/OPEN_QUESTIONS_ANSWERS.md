# Open Questions — Product Owner Answers

Source: the 20 open questions in `BACKLOG.md`. Answered by the PO on 2026-10-08.
Status: BACKLOG.md and sprints updated to these answers on 2026-10-08. No sprint has started.

| # | Topic | PO answer | Status |
|---|-------|-----------|--------|
| 1 | Roles | Agree (Owner = Admin). **Rename Worker → Driver everywhere** (business doc, backlog, project). Roles: **Admin and Manager**. | Need: what can Manager do vs Admin? |
| 2 | Account approval | Yes, drivers/traders must be approved by Admin. | Final |
| 3 | Driver registration fields | "yes or now" (unclear) | **Unclear** |
| 4 | Login identifier | Phone number **or** username. | Final |
| 5 | Forgot password | Yes, via email. | Need: is email a required field at registration? |
| 6 | Shop catalog | Shop has categories > sub-categories > items, with prices, different sizes, and extra items (add-ons). | Final, but a big scope increase over the MVP — see follow-up |
| 7 | Location | Name + address text + optional coordinates. | Final |
| 8 | Client saved addresses | Yes. | Final |
| 9 | Cancellation / assignment | "Orders assigned from Admin in MVP." | Need: does this mean Admin assigns drivers (drivers no longer self-accept)? Who cancels? |
| 10 | Rating | Yes (client rates driver 1–5 + optional comment, optional, driver sees aggregate). | Final |
| 11 | Client on trader-created orders | PO asked for an explanation. | **Pending PO decision** |
| 12 | Order edits before driver accepts | Yes. | Final |
| 13 | Auto-publish | Orders are **reviewed by Admin** before becoming available (not automatic). | Final |
| 14 | Notifications | Yes, in-app only. | Final |
| 15 | Language | (left blank) | **Unanswered** |
| 16 | Driver can un-accept / release stuck order | No. | Final |
| 17 | Driver sees contact phones after accepting | Yes. | Final |
| 18 | Admin permissions | Two roles: Admin, Manager. | Same follow-up as Q1 |
| 19 | Dashboard time filter | Yes. | Final |
| 20 | Prices / fees | Prices and fees are added by Admin. | Need: Admin sets delivery fee per order? Item prices set by trader? |

## Round 2 (2026-10-08)

| # | Decision | Notes |
|---|----------|-------|
| 1/18 | Admin and Manager have the same permissions for now. **Manager cannot create/edit/delete Admin accounts.** | Final |
| 3 | Driver registers with full name, phone, password only. | Final |
| 5 | Forgot password via email. | "okay" was ambiguous: email assumed **optional at registration, required to use recovery**. Confirm. |
| 6 | Simple MVP shop items. Full catalog (categories, sub-categories, sizes, extras, prices) goes to the backlog as a later item. | Final |
| 9 | **Admin/Manager assigns each order to a driver. Drivers do not self-accept.** Cancellation: not answered. | Changes sprints 05 and 08 |
| 11 | "Order created from customer for now." | Interpreted: orders are created by the client. Trader-created orders: confirm if deferred. |
| 15 | UI is Arabic and English (bilingual, RTL/LTR). | Final |
| 20 | Admin sets both delivery fee and item prices. | Final |

Next step (needs PO approval): Business Manager updates BACKLOG.md (Worker→Driver, Manager role, admin assignment, bilingual, email recovery, prices); then Product Manager re-plans sprints.

## Round 3 (2026-10-08) — all questions now answered

- Q11: Trader-created orders move to a **later phase**; MVP orders are created by clients only.
- Q5: Confirmed — email optional at registration, required to use password recovery.
- Q9: Confirmed — client may cancel before the Admin assigns a driver; after assignment only Admin/Manager can cancel.

Status: ready for Business Manager to update BACKLOG.md (needs PO approval to run).
