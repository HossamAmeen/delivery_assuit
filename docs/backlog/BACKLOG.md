# Project Backlog

## Overview
- **Goal:** Deliver a very simple MVP delivery-order app that completes one clear cycle: **Create (client) -> Review (Admin/Manager) -> Available -> Assign (Admin/Manager) -> Pickup -> Delivery -> Delivered**. Any feature that does not directly help finish this cycle is deferred to the Later Phase (SEC-11).
- **Target users:**
  - **Admin (Owner)** - manages and monitors the whole system, including Manager accounts.
  - **Manager** - same permissions as Admin, except that a Manager cannot create, edit, or delete Admin accounts.
  - **Driver (مندوب)** - sees the orders assigned to him, executes them, reviews past orders and performance.
  - **Trader / Shop (تاجر / محل)** - manages shop profile, items, and locations; sees the orders placed to the shop.
  - **Client (عميل)** - orders from a shop or requests a direct place-to-place delivery, tracks own orders.
- **Constraints:**
  - Three user-facing apps (PWAs): Driver, Trader/Shop, Client; plus an Admin/Manager dashboard.
  - Stack per AGENTS.md: Django + DRF backend, Vue 3 frontend, Docker.
  - UI is bilingual Arabic + English (RTL/LTR).
  - MVP is intentionally minimal: no online payment, wallet, commission, accounting, full product catalog, multi-level delivery pricing, route optimization, advanced maps, chat, coupons, loyalty, advanced analytics, subscriptions, ERP, push/SMS notifications, or trader-created orders (see SEC-11). A single delivery fee and item prices set by Admin/Manager are the only price data (BL-077).
  - Business rules from the business document apply everywhere (see "Business Rules" below).
  - Business source: `delivery_app_business_logic.md`. Product Owner decisions: `OPEN_QUESTIONS_ANSWERS.md` (final).

### Order lifecycle (reference)
`CREATED -> AVAILABLE -> ASSIGNED -> PICKED_UP -> IN_DELIVERY -> DELIVERED`, plus `CANCELLED`.
- CREATED: client submitted the order; waiting for Admin/Manager review.
- AVAILABLE: reviewed and approved; waiting for Admin/Manager to assign a driver.
- ASSIGNED: Admin/Manager assigned a driver (drivers never self-accept).
- A rejected review results in CANCELLED.

### Business Rules (reference, referenced by items as BR-N)
- BR-1: A driver may hold only one active order at a time (MVP assumption, see Remaining Assumptions).
- BR-2: A `DELIVERED` order cannot move to any other execution status.
- BR-3: A `CANCELLED` order cannot be assigned to a driver.
- BR-4: Assigning an order links it to the driver; there is no driver accept, un-accept, or release.
- BR-5: Only active, approved drivers can be assigned orders; a driver sees only orders assigned to him.
- BR-6: A client sees only their own orders.
- BR-7: A trader sees only the orders placed to their shop.
- BR-8: Admin and Manager see all orders.
- BR-9: Password change is done from an authenticated account.
- BR-10: A driver's monthly performance is based on the orders he executed and his ratings.
- BR-11: A new order is not visible as AVAILABLE until Admin/Manager reviews and approves it.
- BR-12: Cancellation: the client may cancel until a driver is assigned; after assignment only Admin/Manager can cancel. A DELIVERED order cannot be cancelled.
- BR-13: A client may edit an order only before a driver is assigned.
- BR-14: Admin and Manager have identical permissions, except that Manager cannot create, edit, or delete Admin accounts.
- BR-15: Drivers and traders must be approved by Admin/Manager before they can operate; clients are active immediately.
- BR-16: The driver sees the client's and trader's contact phone numbers only once the order is assigned to him.
- BR-17: Delivery fee and item prices are set by Admin/Manager only.
- BR-18: Orders are created by clients only in MVP.

## Open Questions
All 20 original open questions were answered by the Product Owner. The decisions are final and recorded in `OPEN_QUESTIONS_ANSWERS.md`; they are applied throughout this backlog. Nothing is blocking.

### Remaining Assumptions (to confirm when convenient, non-blocking)
- BR-1 (one active order per driver) was never explicitly confirmed by the PO; kept as an MVP assumption. Admin/Manager cannot assign a new order to a driver who has an active one.
- Username (for login by phone or username): optional unique profile field for all roles; Admin/Manager accounts always have one. Driver registration still asks only name, phone, password.
- Trader and client see the assigned driver's name; the driver's phone is not exposed to them (the PO only specified contact visibility for drivers).

---

## SEC-01: Project Foundation & Setup
**Description:** Create the working skeletons for the backend, the frontends, and the containerized development environment so every later feature has a place to land. Intended for the first sprint.

### BL-001: Backend project skeleton
- **Story:** As a developer, I want a working Django + DRF backend skeleton, so that features can be built on a consistent base.
- **Priority:** Must
- **Scope:** backend
- **Depends on:** —
- **Acceptance criteria:**
  - [ ] The backend project starts locally and responds successfully on a health-check URL.
  - [ ] Configuration (secrets, DB settings, debug flag) is read from environment variables; no secrets are committed.
  - [ ] The backend test suite can be run with one command and at least one sample test passes.
  - [ ] API documentation/browsable schema is reachable in development.
  - [ ] A README section explains how to run the backend and its tests.

### BL-002: Frontend project skeleton
- **Story:** As a developer, I want a working Vue 3 frontend skeleton, so that the Driver, Trader, Client, and Admin/Manager interfaces can be built on a shared base.
- **Priority:** Must
- **Scope:** frontend
- **Depends on:** —
- **Acceptance criteria:**
  - [ ] The frontend app starts in development mode and renders a home page.
  - [ ] The app has a routing structure that clearly separates areas for Driver, Trader, Client, and Admin/Manager.
  - [ ] A shared way to call the backend API (base URL from environment config) exists and is demonstrated by one call to the backend health check.
  - [ ] Unit test runner executes with one command and at least one sample test passes.
  - [ ] A README section explains how to run the frontend and its tests.

### BL-003: Containerized development environment
- **Story:** As a developer, I want the whole system to start with Docker, so that every team member and environment runs the same setup.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-001, BL-002
- **Acceptance criteria:**
  - [ ] A single command starts the backend, frontend, and database together.
  - [ ] The frontend successfully reaches the backend from inside the containers.
  - [ ] Data in the database survives a container restart.
  - [ ] An example environment file (without real secrets) is provided and documented.
  - [ ] A fresh clone can be running by following the README only.

### BL-004: Continuous integration pipeline
- **Story:** As a team, I want automated checks on every change, so that broken code is caught before review.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-001, BL-002
- **Acceptance criteria:**
  - [ ] On every push/merge request, backend tests and frontend tests run automatically.
  - [ ] A failing test makes the pipeline fail visibly.
  - [ ] Linting/format checks for both codebases run in the pipeline.

### BL-005: Installable PWA shell
- **Story:** As a driver, trader, or client, I want to install the app on my phone like a native app, so that I can reach it quickly.
- **Priority:** Should
- **Scope:** frontend
- **Depends on:** BL-002
- **Acceptance criteria:**
  - [ ] The app can be installed to the home screen on a mobile browser, with a name and icon.
  - [ ] The installed app opens full-screen without browser chrome.
  - [ ] The layout is usable on a phone-size screen.

### BL-006: Bilingual support (Arabic + English, RTL/LTR)
- **Story:** As an Arabic- or English-speaking user, I want the interface in my language with the correct text direction, so that I can use the app comfortably.
- **Priority:** Must
- **Scope:** frontend
- **Depends on:** BL-002
- **Acceptance criteria:**
  - [ ] All screens can be shown in Arabic (RTL) and in English (LTR) with a correct layout in each.
  - [ ] The user can switch language, and the choice is remembered.
  - [ ] No user-facing text is hard-coded in a way that blocks adding or changing translations.
  - [ ] Server error messages shown to the user are available in both languages.

### BL-007: Seed/demo data and initial admin account
- **Story:** As the owner, I want a way to create the first Admin account and sample data, so that the system can be started and demonstrated.
- **Priority:** Must
- **Scope:** backend
- **Depends on:** BL-001
- **Acceptance criteria:**
  - [ ] A documented command creates the first Admin account without using the public registration.
  - [ ] An optional documented command loads demo Admin/Manager, drivers, traders, shops, items, clients, locations, and orders in various statuses.
  - [ ] Running the demo-data command twice does not create duplicate or broken data.

---

## SEC-02: Authentication & Accounts
**Description:** Registration, login, logout, password change, password recovery, roles, and profiles for all user types. Corresponds to Phase 1 (Foundation).

### BL-008: User roles and role-based access
- **Story:** As the system owner, I want every account to have exactly one role (Admin, Manager, Driver, Trader, Client), so that each person only sees and does what their role allows.
- **Priority:** Must
- **Scope:** backend
- **Depends on:** BL-001
- **Acceptance criteria:**
  - [ ] Every account has a role of Admin, Manager, Driver, Trader, or Client.
  - [ ] Admin and Manager have identical permissions, except that Manager cannot create, edit, or delete Admin accounts (BR-14).
  - [ ] A user with one role cannot access features of another role (e.g. a client cannot open admin or driver data); the system refuses with a clear "not allowed" response.
  - [ ] Unauthenticated users can only reach registration, login, and password recovery.
  - [ ] Tests exist for each role being allowed and denied on at least one protected action, including Manager being denied on Admin accounts.

### BL-009: Driver registration
- **Story:** As a prospective driver, I want to register with my full name, phone number, and password, so that I can be approved and start receiving assigned orders.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-008
- **Acceptance criteria:**
  - [ ] Registration requires only full name, phone number, and password; missing fields show clear errors. Email is optional.
  - [ ] A phone number already in use cannot be registered again.
  - [ ] Weak passwords are rejected with a clear message.
  - [ ] After registration, the account has the Driver role and the status "pending approval" until Admin/Manager approves it (BL-078).

### BL-010: Trader/Shop registration
- **Story:** As a shop owner, I want to create a trader account, so that my shop can receive client orders once approved.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-008
- **Acceptance criteria:**
  - [ ] Registration captures shop/trader name, contact phone, and password. Email is optional.
  - [ ] A phone number already in use cannot be registered again.
  - [ ] After registration, the account has the Trader role and the status "pending approval" until Admin/Manager approves it (BL-078).

### BL-011: Client registration
- **Story:** As a customer, I want to create a client account, so that I can request deliveries and order from shops.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-008
- **Acceptance criteria:**
  - [ ] Registration captures name, phone number, and password. Email is optional.
  - [ ] A phone number already in use cannot be registered again.
  - [ ] After registration the account has the Client role and is immediately active.

### BL-012: Login (phone or username)
- **Story:** As a registered user, I want to log in with my phone number or my username and password, so that I can access my role's screens.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-009, BL-010, BL-011
- **Acceptance criteria:**
  - [ ] The login identifier accepts either a phone number or a username.
  - [ ] Valid credentials give access and land the user on their role's home screen (Driver: My Assigned Orders; Trader: Dashboard; Client: Home; Admin/Manager: Dashboard).
  - [ ] Invalid credentials show a generic error that does not reveal whether the phone number or username exists.
  - [ ] Accounts pending approval cannot operate and are told that approval is pending; deactivated/blocked accounts cannot log in and are told why in a user-friendly message.
  - [ ] Repeated failed attempts are limited (rate-limited) to protect accounts.
  - [ ] The user stays signed in across page refresh until they log out or the session expires.

### BL-013: Logout
- **Story:** As a user, I want to log out, so that nobody else can use my account on a shared device.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-012
- **Acceptance criteria:**
  - [ ] After logout, protected screens redirect to login.
  - [ ] After logout, the previous session can no longer call protected actions.

### BL-014: Change password
- **Story:** As an authenticated user, I want to change my password, so that I can keep my account secure (BR-9).
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-012
- **Acceptance criteria:**
  - [ ] The user must provide the current password and a new password.
  - [ ] A wrong current password is rejected.
  - [ ] A weak new password is rejected with a clear message.
  - [ ] After a successful change, the new password works and the old one does not.
  - [ ] The action is only possible when logged in.

### BL-015: Profile view and edit (all roles)
- **Story:** As a user, I want to see and edit my profile, so that my details are correct.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-012
- **Acceptance criteria:**
  - [ ] A user can view name, phone number, username and email (if set), account data, and account status.
  - [ ] A user can edit name, phone number, and email; phone number and username must stay unique.
  - [ ] A user can add an email later so that password recovery becomes available.
  - [ ] A user cannot edit their role or account status.
  - [ ] A user can only view/edit their own profile.

### BL-016: Password recovery via email
- **Story:** As a user who forgot my password, I want to recover access through my email, so that I am not locked out.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-012, BL-015
- **Acceptance criteria:**
  - [ ] A user can request recovery by entering their phone number, username, or email; a time-limited, single-use reset link/code is sent to the email on file.
  - [ ] The response is identical whether or not the account exists (no account enumeration).
  - [ ] An account without an email cannot use recovery and is told to contact Admin/Manager; email is optional at registration but required for recovery.
  - [ ] After a successful reset, the new password works, the old one does not, and the reset link/code cannot be reused.
  - [ ] A weak new password is rejected with a clear message.
  - [ ] Recovery requests are rate-limited.

---

## SEC-03: Locations & Branches
**Description:** Places (locations, branches, service points) that can be used as pickup or delivery points. A location is a name + address text + optional coordinates. Traders manage their own; clients provide places per order and can save addresses.

### BL-017: Trader manages locations/branches
- **Story:** As a trader, I want to add, view, edit, and remove my locations/branches, so that clients ordering from my shop have a pickup point.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-010
- **Acceptance criteria:**
  - [ ] A trader can create a location with a name, address text, and optional coordinates (latitude/longitude).
  - [ ] A trader can see a list of only their own locations.
  - [ ] A trader can edit and delete a location; deleting a location used by past orders must not break those orders' history.
  - [ ] Invalid or missing required location data (name, address) shows clear errors; invalid coordinates are rejected.
  - [ ] A trader cannot see or change another trader's locations.

### BL-018: Mark a location as usable for pickup and/or delivery
- **Story:** As a trader, I want to indicate whether a location can be used as a pickup point, a delivery point, or both, so that order creation offers sensible choices.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-017
- **Acceptance criteria:**
  - [ ] Each location has a flag for pickup and for delivery.
  - [ ] When a client orders from a shop, pickup choices show only that shop's pickup-enabled locations.
  - [ ] Changing the flags does not alter existing orders.

### BL-019: Location input for client orders
- **Story:** As a client, I want to enter a pickup or delivery place for my order, so that the driver knows where to go.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-011
- **Acceptance criteria:**
  - [ ] A client can enter pickup and delivery places as name + address text + optional coordinates, without needing an advanced map.
  - [ ] Place data entered for an order is stored with the order and shown to the driver once the order is assigned.
  - [ ] A client can choose one of their saved addresses instead of typing (BL-076).

### BL-020: Shop's default pickup location
- **Story:** As a client ordering from a shop, I want the shop's location to be used automatically as the pickup point, so that I only provide my delivery place.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-017, BL-019
- **Acceptance criteria:**
  - [ ] When ordering from a shop, the pickup point is set from one of the shop's pickup-enabled locations without the client typing it.
  - [ ] If a shop has several pickup locations, the client can choose one.
  - [ ] A shop with no pickup-enabled location cannot receive client orders and shows as unavailable.

---

## SEC-04: Orders & Order Lifecycle
**Description:** The core of the system: client-created orders, Admin/Manager review, statuses, transitions, and visibility rules. Corresponds to Phase 2 (Orders).

### BL-021: Order data and unique reference
- **Story:** As any user, I want every order to carry its essential data and a unique reference number, so that it can be identified and discussed unambiguously.
- **Priority:** Must
- **Scope:** backend
- **Depends on:** BL-008, BL-017
- **Acceptance criteria:**
  - [ ] An order stores: reference number, client (also the creator), trader/shop (optional), driver (optional until assigned), pickup location, delivery location, description, ordered items (for shop orders), delivery fee, status, created time, updated time.
  - [ ] Each order receives a unique, human-readable reference number automatically.
  - [ ] Pickup and delivery locations are mandatory; description is mandatory for direct deliveries.
  - [ ] Timestamps are set automatically.
  - [ ] The delivery fee is empty until set by Admin/Manager (BL-077).

### BL-022: Order status lifecycle and allowed transitions
- **Story:** As the business owner, I want orders to move only through valid statuses, so that the delivery cycle is consistent.
- **Priority:** Must
- **Scope:** backend
- **Depends on:** BL-021
- **Acceptance criteria:**
  - [ ] The valid flow is CREATED -> AVAILABLE -> ASSIGNED -> PICKED_UP -> IN_DELIVERY -> DELIVERED; CANCELLED is an additional terminal state.
  - [ ] CREATED -> AVAILABLE only by Admin/Manager review; AVAILABLE -> ASSIGNED only by Admin/Manager assignment; later execution steps only by the assigned driver.
  - [ ] Any attempt to skip a step or move backwards is rejected with a clear message.
  - [ ] A DELIVERED order cannot be changed to any other execution status (BR-2).
  - [ ] A CANCELLED order cannot be moved to any execution status (BR-3).
  - [ ] Every status change records who made it and when.
  - [ ] Tests cover every valid and every invalid transition.

### BL-023: Admin/Manager reviews orders before they become available
- **Story:** As an Admin or Manager, I want to review each new order and approve or reject it, so that only valid orders reach the drivers (BR-11).
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-022
- **Acceptance criteria:**
  - [ ] A newly created order has status CREATED and does not appear as available.
  - [ ] Admin/Manager sees a "pending review" list of CREATED orders with full details.
  - [ ] Approving moves the order to AVAILABLE (awaiting driver assignment); rejecting moves it to CANCELLED with a reason shown to the client.
  - [ ] Admin/Manager can set the delivery fee during review (BL-077).
  - [ ] Review actions are recorded with who and when.
  - [ ] The client sees "waiting for review" while CREATED and "waiting for a driver" while AVAILABLE.

### BL-024: Order visibility and permissions
- **Story:** As the business owner, I want strict visibility of orders per role, so that users only see what they should.
- **Priority:** Must
- **Scope:** backend
- **Depends on:** BL-021
- **Acceptance criteria:**
  - [ ] A client sees only their own orders (BR-6).
  - [ ] A trader sees only orders placed to their shop (BR-7).
  - [ ] A driver sees only orders assigned to him; never unassigned orders or other drivers' orders.
  - [ ] Admin and Manager see all orders (BR-8).
  - [ ] Requests for an order the user may not see behave as if the order does not exist.
  - [ ] Tests exist for each role against another role's order.

### BL-025: Cancel order
- **Story:** As a client, I want to cancel my order until a driver is assigned, and as Admin/Manager I want to cancel any unfinished order, so that unwanted deliveries are stopped (BR-12).
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-022, BL-024
- **Acceptance criteria:**
  - [ ] The client can cancel their own order while it is CREATED or AVAILABLE (before a driver is assigned).
  - [ ] After a driver is assigned, only Admin/Manager can cancel; the client no longer sees a cancel action.
  - [ ] If a driver was already assigned, that driver sees the order as cancelled and is freed for another assignment.
  - [ ] A DELIVERED order cannot be cancelled by anyone.
  - [ ] A cancelled order remains visible in history with status CANCELLED, who cancelled it, and when.

### BL-026: Edit order before driver assignment
- **Story:** As a client, I want to correct the details of my order before a driver is assigned, so that mistakes do not cause bad deliveries (BR-13).
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-021, BL-022
- **Acceptance criteria:**
  - [ ] The client can edit description, items, and locations while the order is CREATED or AVAILABLE.
  - [ ] Once ASSIGNED or later, editing is refused for the client.
  - [ ] Editing is refused for users who did not create the order (Admin/Manager excepted).
  - [ ] An edit to an AVAILABLE order returns it to CREATED for re-review, or notifies Admin/Manager of the change (Product Manager to pick the simpler option).

### BL-027: Order status history
- **Story:** As a user following an order, I want to see when each status happened, so that I understand its progress.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-022
- **Acceptance criteria:**
  - [ ] Order details show a timeline of status changes with timestamps.
  - [ ] The timeline is visible to the client, the assigned driver, the shop, and Admin/Manager only.

### BL-028: Order list filtering and search
- **Story:** As a user with many orders, I want to filter by status and search by reference, so that I find an order quickly.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-024
- **Acceptance criteria:**
  - [ ] Order lists can be filtered by status.
  - [ ] Order lists can be searched by reference number.
  - [ ] Lists are paginated and sorted newest first by default.
  - [ ] Filters never reveal orders the user is not allowed to see.

---

## SEC-05: Driver (مندوب) Experience
**Description:** Everything the driver does: seeing his assigned orders, executing them, history, performance, and profile. Drivers do not browse or accept orders; Admin/Manager assigns them (BL-031). Driver PWA screens: Login, Register, My Assigned Orders, Order Details, My Orders (history), Performance, Profile.

### BL-029: View my assigned orders
- **Story:** As a driver, I want to see the orders assigned to me and their progress status, so that I know what to deliver.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-031, BL-024
- **Acceptance criteria:**
  - [ ] The list shows only orders assigned to this driver that are not yet finished, with their progress status (ASSIGNED, PICKED_UP, IN_DELIVERY).
  - [ ] Each entry shows reference, pickup, delivery, short description, and time assigned.
  - [ ] Only approved, active drivers can use the list (BR-5); pending/inactive drivers see nothing and are told their account is not active.
  - [ ] The list can be refreshed and shows newest assignments first.
  - [ ] An order cancelled by Admin/Manager disappears from the active list and shows as cancelled in history.

### BL-030: Order details for driver
- **Story:** As a driver, I want to open an assigned order's full details, so that I know exactly what the job involves.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-029
- **Acceptance criteria:**
  - [ ] Details show reference, pickup, delivery, description, items (if any), trader/shop (if any), and status.
  - [ ] The client's and trader's contact phone numbers are shown only once the order is assigned to this driver (BR-16).
  - [ ] A driver cannot open details of an order not assigned to him.

### BL-031: Admin/Manager assigns an order to a driver
- **Story:** As an Admin or Manager, I want to assign an available order to a driver, so that the delivery gets executed (BR-4). (Replaces the former driver "accept" flow; moved here from SEC-05, ID unchanged.)
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-023, BL-022, BL-078
- **Acceptance criteria:**
  - [ ] Admin/Manager can assign only AVAILABLE orders, choosing from active, approved drivers.
  - [ ] Assigning changes the status to ASSIGNED and links the order to the chosen driver.
  - [ ] A driver who already has an active order cannot be assigned another (BR-1).
  - [ ] A CANCELLED order cannot be assigned (BR-3).
  - [ ] Two Admin/Manager users assigning the same order at the same time: exactly one succeeds, the other gets a clear message.
  - [ ] The assignment is recorded with who and when, and the driver and client are notified (BL-066).
  - [ ] Drivers have no accept, un-accept, or release action anywhere in the system.

### BL-032: Execute order - pickup, in delivery, delivered
- **Story:** As a driver, I want to update the order as I pick it up, drive, and deliver, so that everyone sees real progress.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-031
- **Acceptance criteria:**
  - [ ] The driver can mark ASSIGNED -> PICKED_UP, PICKED_UP -> IN_DELIVERY, IN_DELIVERY -> DELIVERED in that order only.
  - [ ] Only the driver assigned to the order can change its execution status.
  - [ ] Each step shows only the one valid next action button.
  - [ ] After DELIVERED, the order moves to My Orders (previous orders) and the driver is free for a new assignment.
  - [ ] A DELIVERED order can no longer be changed (BR-2).

### BL-033: Driver's active order view
- **Story:** As a driver, I want a clear view of my current order, so that I can continue it quickly after reopening the app.
- **Priority:** Must
- **Scope:** frontend
- **Depends on:** BL-031
- **Acceptance criteria:**
  - [ ] If the driver has an active order, it is shown prominently on the home screen.
  - [ ] The view offers the next valid status action.
  - [ ] When no active order exists, a friendly "no assigned orders" state is shown.

### BL-034: My Orders (previous orders)
- **Story:** As a driver, I want to see my previous orders, so that I can review my work history.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-032
- **Acceptance criteria:**
  - [ ] Lists the driver's delivered and cancelled orders, newest first, with reference, status, and dates.
  - [ ] Opening an entry shows the order details.
  - [ ] Only the driver's own orders appear.
  - [ ] The list is paginated.

### BL-035: RETIRED - Driver release/withdraw from an accepted order
- **Status:** Removed by PO decision (no driver un-accept, no release; drivers do not accept). The ID is retired and must not be reused.

### BL-036: Driver profile
- **Story:** As a driver, I want a profile screen with my name, phone, account data, and status, so that I can verify and manage my account.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-015
- **Acceptance criteria:**
  - [ ] Shows name, phone, account data, and account status (pending/active/inactive).
  - [ ] Provides access to Change Password (BL-014) and Logout (BL-013).
  - [ ] Driver cannot change their own account status.

---

## SEC-06: Trader / Shop Experience
**Description:** Everything a trader does in MVP: dashboard, shop profile and items, locations, tracking the orders placed to the shop, profile. Traders do not create orders in MVP (see BL-037 in SEC-11). Trader PWA screens: Login, Register, Dashboard, My Orders, Shop Items, Locations/Branches, Profile.

### BL-037: MOVED to SEC-11 (Later Phase)
- **Status:** Trader-created delivery orders are deferred (BR-18). Full item is in SEC-11. The ID is unchanged.

### BL-038: Trader's orders list and tracking
- **Story:** As a trader, I want to see the orders clients placed to my shop and follow their status, so that I can prepare them (BR-7).
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-024, BL-047
- **Acceptance criteria:**
  - [ ] Lists only orders placed to this trader's shop (and approved to proceed), newest first, with reference, status, pickup, delivery, and date.
  - [ ] Opening an order shows its details and current status.
  - [ ] The list can be filtered by status (BL-028).
  - [ ] Status changes are reflected when the page is refreshed.
  - [ ] The trader cannot create, edit, or cancel orders.

### BL-039: See the assigned driver
- **Story:** As a trader, I want to see which driver was assigned to my shop's order, so that I can coordinate the handover.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-031, BL-038
- **Acceptance criteria:**
  - [ ] Before assignment, no driver is shown ("waiting for a driver").
  - [ ] After assignment, the driver's name is displayed (phone not exposed to traders, see Remaining Assumptions).
  - [ ] If Admin/Manager cancels the order, the order shows as cancelled.

### BL-040: Trader dashboard
- **Story:** As a trader, I want a simple dashboard of my shop's orders, so that I get a quick overview.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-038
- **Acceptance criteria:**
  - [ ] Shows counts of the shop's orders: total, waiting for driver, in progress, delivered, cancelled.
  - [ ] Counts match the trader's order list.
  - [ ] Shows only the trader's own data.

### BL-041: Trader shop profile and availability
- **Story:** As a trader, I want to manage my shop details and mark my shop as open/available, so that clients only see me when I can take orders.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-015, BL-010
- **Acceptance criteria:**
  - [ ] Trader can edit shop name, phone, and a short description.
  - [ ] Trader can switch the shop between available and unavailable.
  - [ ] Unavailable shops do not appear in the client's Shops list (BL-045).
  - [ ] Trader can reach Change Password and Logout.

### BL-042: Shop items list (simple)
- **Story:** As a trader, I want to list the items my shop offers, so that clients can choose what to order.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-041
- **Acceptance criteria:**
  - [ ] Trader can add, edit, and remove simple items (name and optional short description) in a single flat list.
  - [ ] Item prices are set by Admin/Manager, not by the trader (BL-077, BR-17); an item without a price is shown without one.
  - [ ] Trader sees only their own items.
  - [ ] Items can be hidden without deleting them.
  - [ ] No catalog features (categories, sub-categories, sizes, extras) are included in MVP; they are in BL-074.

### BL-043: Trader approval and status effects
- **Story:** As the owner, I want trader accounts to respect their approval/active status, so that only approved shops can operate.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-010, BL-078
- **Acceptance criteria:**
  - [ ] A trader pending approval or inactive cannot use the trader app and sees a clear message.
  - [ ] A trader that is pending or inactive does not appear to clients.
  - [ ] Existing orders of an inactive trader remain visible to Admin/Manager.

---

## SEC-07: Client Experience
**Description:** The client's two paths: ordering from a shop and direct place-to-place delivery, plus order tracking, saved addresses, and profile. Orders are created by clients only. Client PWA screens: Login, Register, Home, Shops, Shop Details, Create Delivery, My Orders, Order Details, Saved Addresses, Profile.

### BL-044: Client home
- **Story:** As a client, I want a simple home screen offering my two options, so that I can start quickly.
- **Priority:** Must
- **Scope:** frontend
- **Depends on:** BL-012
- **Acceptance criteria:**
  - [ ] Home presents two clear entries: "Order from a shop" and "Deliver from place to place".
  - [ ] Home gives quick access to My Orders and Profile.
  - [ ] Home may show the client's most recent active order.

### BL-045: Browse available shops
- **Story:** As a client, I want to see the shops that are available, so that I can choose where to order from.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-041, BL-020
- **Acceptance criteria:**
  - [ ] The list shows only approved, active, available traders that can accept orders.
  - [ ] Each entry shows shop name and a short description.
  - [ ] The list can be searched by shop name.
  - [ ] An empty list shows a friendly "no shops available" message.

### BL-046: Shop details
- **Story:** As a client, I want to open a shop and see what it offers, so that I can decide what to order.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-045
- **Acceptance criteria:**
  - [ ] Shop details show shop name, description, and its visible items with prices where set (BL-042).
  - [ ] Hidden items are not shown.
  - [ ] A shop that becomes unavailable cannot be ordered from.

### BL-047: Order from a shop (Scenario C)
- **Story:** As a client, I want to choose items from a shop and set my delivery place, so that a driver brings them to me.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-046, BL-019, BL-020
- **Acceptance criteria:**
  - [ ] The client picks one or more items (with quantities) from the shop's item list, optionally adds a free-text note, and gives a delivery place.
  - [ ] The pickup point is taken from the shop (BL-020).
  - [ ] On success the order is created with the client and shop recorded, a reference number is generated, and the status is CREATED (waiting for Admin/Manager review, BL-023).
  - [ ] The client sees a confirmation with the reference number.
  - [ ] Missing item or delivery place blocks creation with clear errors.
  - [ ] The order appears in the shop's order list once approved (BL-038).

### BL-048: Direct place-to-place delivery (Scenario D)
- **Story:** As a client, I want to request a delivery from any pickup point to any delivery point, so that I can send something without choosing a shop.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-019
- **Acceptance criteria:**
  - [ ] The client enters pickup point, delivery point, order details, and optional notes.
  - [ ] Pickup, delivery, and details are mandatory; notes are optional.
  - [ ] On success the order has no trader, the client is recorded, a reference number is generated, and the status is CREATED (waiting for review).
  - [ ] The client sees a confirmation with the reference number.

### BL-049: Client's orders list
- **Story:** As a client, I want to see all my orders, so that I can follow them (BR-6).
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-024, BL-047, BL-048
- **Acceptance criteria:**
  - [ ] Lists only the client's own orders, newest first, with reference, status, and date.
  - [ ] Can be filtered by status and shows active orders clearly.
  - [ ] The list is paginated.

### BL-050: Client order details and tracking
- **Story:** As a client, I want to open an order and see its current status and driver, so that I know when to expect delivery.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-049, BL-027
- **Acceptance criteria:**
  - [ ] Shows reference, pickup, delivery, description, items, delivery fee (if set), current status, and status timeline.
  - [ ] Shows "waiting for review" (CREATED) or "waiting for a driver" (AVAILABLE) before assignment.
  - [ ] Shows the assigned driver's name after assignment.
  - [ ] Status updates appear on refresh.
  - [ ] A client cannot open another client's order.
  - [ ] The client can edit (BL-026) and cancel (BL-025) the order from this screen only while allowed (before driver assignment).

### BL-051: Rate driver after delivery
- **Story:** As a client, I want to rate the driver after my order is delivered, so that good service is recognised.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-050, BL-061
- **Acceptance criteria:**
  - [ ] Rating is offered only on DELIVERED orders of this client, and is optional.
  - [ ] Rating is a score of 1 to 5 with an optional comment.
  - [ ] An order can be rated once only.
  - [ ] The rating feeds the driver's performance (see SEC-09).

### BL-076: Client saved addresses
- **Story:** As a client, I want to save my addresses and reuse them, so that I do not retype them for every order.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-011, BL-019
- **Acceptance criteria:**
  - [ ] A client can add, view, edit, and delete saved addresses, each with a name, address text, and optional coordinates.
  - [ ] When creating an order, the client can pick a saved address for pickup or delivery, or enter a new one (with an option to save it).
  - [ ] A client sees and manages only their own saved addresses.
  - [ ] Deleting or editing a saved address does not change past orders.

---

## SEC-08: Admin / Manager Dashboard & Management
**Description:** Simple dashboard with cards plus management of users, approvals, traders, drivers, clients, and orders (review, assignment, pricing). Admin and Manager have the same permissions, except that Manager cannot create, edit, or delete Admin accounts (BR-14). Corresponds to Phase 4 (Admin). No financial functions beyond delivery fee and item prices in MVP.

### BL-052: Account activate/deactivate
- **Story:** As an Admin or Manager, I want to activate or deactivate any non-admin account, so that I control who can use the system.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-008
- **Acceptance criteria:**
  - [ ] Admin/Manager can change a driver, trader, client, or (Admin only) manager account between active and inactive; Manager cannot change Admin accounts.
  - [ ] An inactive user cannot log in or use the system (see BL-012).
  - [ ] Deactivating a driver with an active order does not lose the order: it stays assigned and visible to Admin/Manager, who can cancel it (BL-055).
  - [ ] Each change is recorded with who and when.

### BL-053: Dashboard cards with time filter
- **Story:** As an Admin or Manager, I want a dashboard with summary cards filterable by period, so that I see the state of the system at a glance.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-008
- **Acceptance criteria:**
  - [ ] Drivers card shows total drivers with Active, Inactive, and Pending-approval counts.
  - [ ] Traders/Shops card shows total with Active, Inactive, and Pending-approval counts.
  - [ ] Clients card shows total clients.
  - [ ] Orders card shows total, Pending, In Progress, Delivered, and Cancelled counts.
  - [ ] Order counts can be filtered by a time period (e.g. today, this week, this month, custom range); the default is all-time.
  - [ ] Counts match the underlying data (verified by tests with known data).
  - [ ] Pending maps to CREATED/AVAILABLE; In Progress maps to ASSIGNED/PICKED_UP/IN_DELIVERY (documented on screen or in help text).

### BL-054: Admin/Manager orders table
- **Story:** As an Admin or Manager, I want a table of all orders, so that I can monitor and follow them (BR-8).
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-024
- **Acceptance criteria:**
  - [ ] The table shows reference, client, trader/shop (if any), driver, pickup, delivery, status, delivery fee, and created-at.
  - [ ] Can be filtered by status and by time period, and searched by reference.
  - [ ] Shows all orders regardless of client.
  - [ ] Paginated, newest first.
  - [ ] Clicking a row opens the order details with its status timeline and the available actions (review, assign, cancel).

### BL-055: Admin/Manager cancels orders
- **Story:** As an Admin or Manager, I want to cancel any unfinished order, so that operations are not blocked.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-054, BL-025
- **Acceptance criteria:**
  - [ ] Admin/Manager can cancel any order not yet DELIVERED, including after a driver is assigned, with a reason.
  - [ ] Cancellation respects the lifecycle rules (BR-2, BR-3) and is recorded with who and when.
  - [ ] There is no release/un-assign flow for drivers.

### BL-056: Admin drivers management
- **Story:** As an Admin or Manager, I want a drivers list and driver details, so that I can review and manage them.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-052, BL-078
- **Acceptance criteria:**
  - [ ] Lists all drivers with name, phone, status (pending/active/inactive), and number of delivered orders.
  - [ ] Can be searched by name/phone and filtered by status.
  - [ ] Driver details show profile data, order history, and performance summary.
  - [ ] Admin/Manager can approve or activate/deactivate from here.

### BL-057: Admin traders/shops management
- **Story:** As an Admin or Manager, I want a traders/shops list and details, so that I can review and manage them.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-052, BL-078
- **Acceptance criteria:**
  - [ ] Lists all traders with shop name, phone, status (pending/active/inactive), and number of orders.
  - [ ] Can be searched and filtered by status.
  - [ ] Trader details show profile data, locations/branches, items, and their orders.
  - [ ] Admin/Manager can approve or activate/deactivate from here, and set item prices (BL-077).

### BL-058: Admin clients management
- **Story:** As an Admin or Manager, I want a clients list and details, so that I can review client accounts and their orders.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-052
- **Acceptance criteria:**
  - [ ] Lists all clients with name, phone, status, and number of orders.
  - [ ] Can be searched by name/phone.
  - [ ] Client details show profile data and order history.
  - [ ] Admin/Manager can activate/deactivate from here.

### BL-059: Users overview and Admin/Manager account management
- **Story:** As an Admin or Manager, I want one place to see and manage all users, so that I can review user data and permissions.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-052
- **Acceptance criteria:**
  - [ ] Shows all users with name, phone, role, and status.
  - [ ] Can be filtered by role and status and searched by name/phone.
  - [ ] Admin can create, edit, and delete Admin and Manager accounts.
  - [ ] Manager can create, edit, and delete Manager accounts and other non-admin users, but cannot create, edit, or delete Admin accounts (BR-14); the system refuses with a clear message.
  - [ ] Only Admin and Manager can access this screen.

### BL-060: Overview of driver performance
- **Story:** As an Admin or Manager, I want a basic overview of driver performance, so that I can see who performs well.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-062
- **Acceptance criteria:**
  - [ ] Shows per driver: delivered count, cancelled count, average rating, and monthly performance.
  - [ ] Can be sorted by delivered count and rating.
  - [ ] Figures match the underlying orders and ratings.
  - [ ] No advanced analytics (charts beyond basic, exports) in MVP.

### BL-077: Admin/Manager sets delivery fee and item prices
- **Story:** As an Admin or Manager, I want to set the delivery fee of each order and the price of each shop item, so that clients see the cost of their order (BR-17).
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-021, BL-042, BL-023
- **Acceptance criteria:**
  - [ ] Admin/Manager can set a price on any shop item; clients see item prices on shop details.
  - [ ] Admin/Manager can set or change the delivery fee on an order during review or later until DELIVERED; the change is recorded with who and when.
  - [ ] Traders, drivers, and clients cannot set or change any price or fee.
  - [ ] The client sees the item prices and delivery fee on the order; changing an item price later does not alter the prices already stored on past orders.
  - [ ] No online payment, wallet, or commission is involved (see BL-070, BL-071).

### BL-078: Admin/Manager approves driver and trader registrations
- **Story:** As an Admin or Manager, I want to approve or reject new driver and trader accounts, so that only vetted people operate in the system (BR-15).
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-009, BL-010, BL-008
- **Acceptance criteria:**
  - [ ] A "pending approval" list shows new driver and trader registrations with their submitted data.
  - [ ] Approving makes the account active; rejecting keeps it unable to operate, with an optional reason.
  - [ ] Pending drivers cannot be assigned orders; pending traders do not appear to clients.
  - [ ] Each decision is recorded with who and when.
  - [ ] The user can see their approval state on login (pending/approved/rejected).

---

## SEC-09: Driver Performance & Ratings
**Description:** Performance data for the driver and for Admin/Manager, based on executed orders and ratings (BR-10).

### BL-061: Rating data model and rules
- **Story:** As the business owner, I want ratings recorded against delivered orders, so that driver quality can be measured.
- **Priority:** Should
- **Scope:** backend
- **Depends on:** BL-032
- **Acceptance criteria:**
  - [ ] A rating is linked to exactly one delivered order and the driver who delivered it.
  - [ ] Only the order's client can rate it (client rates driver), only once, and rating is optional.
  - [ ] Ratings cannot be given to orders that are not DELIVERED.
  - [ ] The score must be 1 to 5; the comment is optional and length-limited.

### BL-062: Driver performance calculation
- **Story:** As the business owner, I want accurate performance numbers per driver, so that they can be shown to drivers and Admin/Manager.
- **Priority:** Must
- **Scope:** backend
- **Depends on:** BL-032
- **Acceptance criteria:**
  - [ ] Calculates executed (delivered) orders count.
  - [ ] Calculates cancelled orders count (orders assigned to the driver that were later cancelled).
  - [ ] Calculates average rating and number of ratings (shows "no ratings yet" when none).
  - [ ] Calculates the same metrics per calendar month (BR-10).
  - [ ] Tests verify the numbers against known sample data, including month boundaries.

### BL-063: Driver performance screen
- **Story:** As a driver, I want to see my performance, so that I know how I am doing.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-062
- **Acceptance criteria:**
  - [ ] Shows executed orders, cancelled orders, aggregate rating (average and count), and monthly performance.
  - [ ] The driver sees only the aggregate rating, not individual ratings or comments per order.
  - [ ] The driver can pick or see a month and the figures update accordingly.
  - [ ] Shows only the logged-in driver's own data.
  - [ ] Shows a friendly empty state for a new driver with no history.

---

## SEC-10: Notifications, Validation & Polish
**Description:** Phase 5 items that improve quality and usability without changing the core cycle.

### BL-064: Input validation and clear error messages
- **Story:** As any user, I want clear, friendly messages when something is wrong, so that I can fix it myself.
- **Priority:** Must
- **Scope:** both
- **Depends on:** BL-002
- **Acceptance criteria:**
  - [ ] Every form shows field-level errors for missing or invalid input, in Arabic and English.
  - [ ] Server validation is enforced even if the screen validation is bypassed.
  - [ ] Phone number format validation is consistent on all forms.
  - [ ] Unexpected server errors show a generic friendly message and never expose internal details.

### BL-065: Global error, loading, and empty states
- **Story:** As any user, I want the app to tell me when it is loading, empty, or offline, so that I am never confused.
- **Priority:** Should
- **Scope:** frontend
- **Depends on:** BL-002
- **Acceptance criteria:**
  - [ ] Every list and details screen has loading, empty, and error states.
  - [ ] Losing connection shows a clear message and a retry option.
  - [ ] An expired session redirects to login without data loss on the current form where feasible.

### BL-066: In-app notifications
- **Story:** As a user following an order, I want to be notified inside the app of important changes, so that I do not have to keep checking.
- **Priority:** Should
- **Scope:** both
- **Depends on:** BL-022
- **Acceptance criteria:**
  - [ ] Admin/Manager are notified when a new order is waiting for review, and when a new driver or trader is waiting for approval.
  - [ ] The driver is notified when an order is assigned to him or cancelled.
  - [ ] The client is notified when the order is approved, assigned, picked up, in delivery, delivered, rejected, or cancelled.
  - [ ] Users see only notifications about their own orders and accounts.
  - [ ] Notifications can be marked as read.
  - [ ] In-app only; no push, SMS, or email notifications (email is used only for password recovery, BL-016).

### BL-067: Auto-refresh of order data
- **Story:** As a driver, trader, client, or Admin/Manager, I want screens to update without a manual refresh, so that statuses are current.
- **Priority:** Could
- **Scope:** both
- **Depends on:** BL-029, BL-050
- **Acceptance criteria:**
  - [ ] Assigned-orders, order status, and review/assignment screens refresh at a regular interval or on event.
  - [ ] Refreshing does not interrupt user input or lose the user's place.

### BL-068: Basic UX improvements
- **Story:** As any user, I want a smooth, consistent, mobile-friendly interface, so that using the app is easy.
- **Priority:** Should
- **Scope:** frontend
- **Depends on:** BL-005
- **Acceptance criteria:**
  - [ ] Navigation is consistent across Driver, Trader, and Client apps.
  - [ ] Primary actions are reachable on small phone screens.
  - [ ] Confirmation is requested before irreversible actions (cancel order, deactivate account).

### BL-069: Account and action audit trail
- **Story:** As the owner, I want key actions logged, so that disputes can be investigated.
- **Priority:** Could
- **Scope:** backend
- **Depends on:** BL-022, BL-052
- **Acceptance criteria:**
  - [ ] Status changes, reviews, assignments, cancellations, approvals, price/fee changes, and account activation changes are recorded with user and time.
  - [ ] Only Admin and Manager can read the log.
  - [ ] The log is never editable through the application.

---

## SEC-11: Later Phase (Not in MVP)
**Description:** Deferred items, recorded so they are not built by accident. Revisit after the MVP success criteria are met.

### BL-037: Trader creates a delivery order
- **Story:** As a trader, I want to create a delivery order by choosing pickup, delivery, and details, so that a driver can deliver it (former Scenario A).
- **Priority:** Could
- **Scope:** both
- **Depends on:** BL-017, BL-021, BL-023, BL-031
- **Acceptance criteria:**
  - [ ] Deferred beyond MVP by PO decision (orders are created by clients only, BR-18).
  - [ ] When built: the trader selects pickup and delivery locations and enters details; the order is CREATED and goes through the same Admin/Manager review (BL-023) and assignment (BL-031) as client orders.
  - [ ] When built: the trader is recorded as creator and trader; how the end customer's name/phone is captured is decided at that time.

### BL-074: Full shop catalog
- **Story:** As a trader, I want a full catalog with categories, sub-categories, items, sizes, extras (add-ons), and prices, so that clients can order from a rich menu.
- **Priority:** Could
- **Scope:** both
- **Depends on:** BL-042, BL-077
- **Acceptance criteria:**
  - [ ] Not built in MVP; only the simple items list in BL-042 is allowed.
  - [ ] When built: a shop has categories > sub-categories > items; each item can have different sizes and extra items (add-ons), each with prices; order totals are computed from the selections.
  - [ ] When built: it replaces the flat item list without breaking past orders.

### BL-070: Online payment and wallet
- **Story:** As a user, I want to pay online and hold a wallet balance, so that I do not handle cash.
- **Priority:** Won't
- **Scope:** both
- **Depends on:** —
- **Acceptance criteria:**
  - [ ] Not built in MVP; no payment or balance fields appear in any screen.

### BL-071: Commissions, accounting, and multi-level delivery pricing
- **Story:** As the owner, I want commissions, accounting, and multi-level delivery pricing, so that I can run the business financially.
- **Priority:** Won't
- **Scope:** both
- **Depends on:** —
- **Acceptance criteria:**
  - [ ] Not built in MVP. Only the single delivery fee and item prices set by Admin/Manager (BL-077) exist; there is no commission, accounting, or pricing tiers.

### BL-072: Advanced maps, navigation, and route optimization
- **Story:** As a driver, I want turn-by-turn navigation and optimized routes, so that I deliver faster.
- **Priority:** Won't
- **Scope:** both
- **Depends on:** —
- **Acceptance criteria:**
  - [ ] Not built in MVP.

### BL-073: Chat, coupons, loyalty, subscriptions
- **Story:** As a user, I want chat, coupons, loyalty rewards, and subscriptions, so that engagement grows.
- **Priority:** Won't
- **Scope:** both
- **Depends on:** —
- **Acceptance criteria:**
  - [ ] Not built in MVP.

### BL-075: Advanced analytics and ERP features
- **Story:** As the owner, I want advanced reports and ERP capabilities, so that I can run the company deeply.
- **Priority:** Won't
- **Scope:** both
- **Depends on:** —
- **Acceptance criteria:**
  - [ ] Not built in MVP; the Admin/Manager dashboard stays limited to the cards and tables in SEC-08.

---

## MVP Success Criteria (traceability)
| # | Criterion | Covered by |
|---|-----------|-----------|
| 1 | A client can create an order (from a shop or direct) | BL-047, BL-048 |
| 2 | Admin/Manager reviews the order and it becomes available | BL-023 |
| 3 | Admin/Manager assigns the order to a driver | BL-031 |
| 4 | The driver executes the assigned order | BL-032 |
| 5 | The order reaches DELIVERED | BL-022, BL-032 |
| 6 | The client can follow the order | BL-049, BL-050 |
| 7 | Admin/Manager can see users and orders | BL-054, BL-056, BL-057, BL-058, BL-059 |
| 8 | The driver sees assigned orders, previous orders, and performance | BL-029, BL-034, BL-063 |
| 9 | The client can create a direct place-to-place delivery | BL-048 |
| 10 | Admin/Manager approves drivers and traders | BL-078 |
