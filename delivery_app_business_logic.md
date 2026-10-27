# Delivery App — Business Logic

## 1. Product Overview

تطبيق توصيل طلبات بسيط جدًا (MVP) يربط بين:
- **Admin / Owner**: إدارة ومتابعة المنظومة.
- **Manager / مدير**: نفس صلاحيات الـAdmin، ولكن لا يستطيع إنشاء أو تعديل أو حذف حسابات الـAdmin.
- **Driver / مندوب**: ينفذ الطلبات التي يتم إسنادها له، ويتابع طلباته السابقة وأداءه.
- **Trader / محل / تاجر**: يدير بيانات المحل ومنتجاته وفروعه، ويتابع الطلبات الموجهة لمحله.
- **Client / عميل**: ينشئ طلبات التوصيل من مكان إلى مكان، ويمكنه أيضًا اختيار محل/تاجر متاح وطلب منتجاته.

الهدف في الـMVP هو تقديم أقل عدد ممكن من الشاشات والعمليات مع الحفاظ على دورة طلب واضحة.

الواجهة ثنائية اللغة: عربي (RTL) وإنجليزي (LTR).

---

# 2. User Roles

## 2.1 Admin / Owner

مسؤول عن إدارة ومتابعة النظام.

### يستطيع:
- رؤية Dashboard مع فلتر زمني.
- رؤية عدد المندوبين (Drivers).
- رؤية عدد التجار والمحلات.
- رؤية عدد العملاء.
- رؤية عدد الطلبات.
- مراجعة الطلبات الجديدة والموافقة عليها أو رفضها قبل أن تصبح متاحة.
- إسناد كل طلب إلى مندوب.
- إلغاء أي طلب لم يتم تسليمه.
- متابعة الطلبات وحالاتها.
- الموافقة على حسابات المندوبين والتجار الجدد.
- تحديد رسوم التوصيل وأسعار المنتجات.
- متابعة أداء المندوبين.
- مراجعة بيانات المستخدمين.
- إدارة الحسابات والصلاحيات، بما في ذلك حسابات الـManager.

> ملاحظة: في الـMVP لا نضيف وظائف مالية (غير رسوم التوصيل وأسعار المنتجات) أو ERP أو تقارير معقدة إلا عند الحاجة.

## 2.2 Manager / مدير

- له نفس صلاحيات الـAdmin.
- استثناء: لا يستطيع إنشاء أو تعديل أو حذف حسابات الـAdmin.

---

## 2.3 Driver / مندوب

المندوب هو الشخص الذي ينفذ طلبات التوصيل. المندوب لا يقبل الطلبات بنفسه؛ الـAdmin/Manager هو الذي يسند الطلب إليه.

### التسجيل
- الاسم بالكامل.
- رقم الهاتف.
- كلمة المرور.
- (البريد الإلكتروني اختياري، ومطلوب فقط لاستعادة كلمة المرور.)
- الحساب لا يعمل إلا بعد موافقة الـAdmin/Manager.

### بعد تسجيل الدخول يرى:
1. **الطلبات المسندة إليه وحالة تقدمها**
2. **طلباتي السابقة**
3. **تقييم / أداء المندوب**
4. **الملف الشخصي**

### الملف الشخصي
- الاسم.
- رقم الهاتف.
- تغيير كلمة المرور.
- بيانات الحساب.
- حالة الحساب.

### الأداء
يمكن عرض:
- عدد الطلبات المنفذة.
- عدد الطلبات الملغاة.
- التقييم (المتوسط والعدد فقط، دون تقييمات فردية).
- تقييم شهري / Monthly Performance.

### دورة طلب المندوب
1. الـAdmin/Manager يسند الطلب إلى المندوب.
2. يظهر الطلب للمندوب في قائمة طلباته المسندة.
3. يفتح تفاصيل الطلب، ويرى أرقام هواتف العميل/التاجر بعد الإسناد فقط.
4. يستلم الطلب من نقطة الاستلام (PICKED_UP).
5. يوصل الطلب إلى نقطة التسليم (IN_DELIVERY).
6. يحدد الطلب كمُسلّم (DELIVERED).
7. ينتقل الطلب إلى الطلبات السابقة.

لا يوجد قبول أو رفض أو إرجاع للطلب من جهة المندوب.

---

# 3. Trader / Shop

التاجر أو المحل يدير بيانات محله ويتابع الطلبات الموجهة له. إنشاء الطلبات من جهة التاجر مؤجل لمرحلة لاحقة.

### التسجيل / الدخول
- إنشاء حساب (بعد موافقة الـAdmin/Manager).
- تسجيل الدخول.
- إدارة الملف الشخصي.

### يستطيع:
- إدارة بيانات المحل وتحديد إن كان متاحًا أم لا.
- إدارة قائمة بسيطة بمنتجات المحل (الاسم ووصف قصير)؛ الأسعار يحددها الـAdmin/Manager.
- إدارة الأماكن / الفروع (نقاط الاستلام).
- رؤية الطلبات الموجهة لمحله ومتابعة حالتها.
- رؤية المندوب المسند للطلب.

### الأماكن المتاحة

التاجر يمكنه إدارة:
- الأماكن / الفروع / نقاط الخدمة المتاحة لديه.
- بيانات المكان: الاسم + العنوان (نص) + إحداثيات اختيارية.
- إمكانية استخدام المكان كنقطة استلام أو تسليم.

---

# 4. Client / العميل

العميل هو الذي ينشئ الطلبات في الـMVP، ولديه مساران بسيطان. يمكنه حفظ عناوينه وإعادة استخدامها.

## المسار الأول: الطلب من محل / تاجر

1. العميل يسجل الدخول.
2. يرى المحلات / التجار المتاحين.
3. يختار محلًا.
4. يرى المنتجات المتاحة لدى المحل.
5. يختار ما يريد.
6. يحدد مكان التسليم.
7. ينشئ الطلب.
8. ينتظر مراجعة الـAdmin/Manager ثم إسناد مندوب.
9. يتابع حالة الطلب.

## المسار الثاني: توصيل من مكان إلى مكان

العميل لا يحتاج إلى اختيار محل.

يدخل:
- نقطة الاستلام.
- نقطة التسليم.
- تفاصيل الطلب.
- أي ملاحظات مطلوبة.

ثم ينشئ طلب توصيل مباشر.

## التعديل والإلغاء والتقييم
- يستطيع العميل تعديل الطلب قبل إسناده لمندوب.
- يستطيع العميل إلغاء الطلب قبل إسناده لمندوب؛ بعد الإسناد يلغيه الـAdmin/Manager فقط.
- بعد التسليم يقيّم المندوب من 1 إلى 5 مع تعليق اختياري (التقييم اختياري).

---

# 5. Order

الـOrder هو العنصر الأساسي في النظام.

### بيانات أساسية مقترحة

- `id`
- `reference_number`
- `client` — هو منشئ الطلب.
- `trader` — اختياري.
- `driver` — اختياري حتى يتم الإسناد.
- `pickup_location`
- `delivery_location`
- `description` / العناصر المطلوبة
- `delivery_fee` — يحددها الـAdmin/Manager.
- `status`
- `created_at`
- `updated_at`

---

# 6. Order Status

الـMVP يستخدم دورة بسيطة:

```text
CREATED
   ↓   (مراجعة Admin/Manager)
AVAILABLE
   ↓   (إسناد من Admin/Manager إلى مندوب)
ASSIGNED
   ↓
PICKED_UP
   ↓
IN_DELIVERY
   ↓
DELIVERED
```

حالات إضافية:

```text
CANCELLED
```

### معنى الحالات

- **CREATED**: العميل أنشأ الطلب وينتظر مراجعة الـAdmin/Manager.
- **AVAILABLE**: تمت الموافقة على الطلب وينتظر إسناد مندوب.
- **ASSIGNED**: الـAdmin/Manager أسند الطلب إلى مندوب.
- **PICKED_UP**: المندوب استلم الطلب.
- **IN_DELIVERY**: الطلب في الطريق.
- **DELIVERED**: تم التسليم.
- **CANCELLED**: الطلب تم إلغاؤه (أو رُفض عند المراجعة).

---

# 7. Dashboard

الـAdmin/Manager Dashboard يكون بسيطًا باستخدام Cards، مع إمكانية الفلترة بفترة زمنية.

### Cards

- **Drivers**
  - إجمالي المندوبين.
  - Active / Inactive / Pending approval.

- **Traders / Shops**
  - إجمالي التجار والمحلات.
  - Active / Inactive / Pending approval.

- **Clients**
  - إجمالي العملاء.

- **Orders**
  - إجمالي الطلبات.
  - Pending (CREATED / AVAILABLE).
  - In Progress (ASSIGNED / PICKED_UP / IN_DELIVERY).
  - Delivered.
  - Cancelled.

### Orders Table

يعرض:
- رقم الطلب.
- العميل.
- التاجر / المحل إن وجد.
- المندوب.
- Pickup.
- Delivery.
- Status.
- Delivery fee.
- Created At.

---

# 8. Applications / Interfaces

نقسم النظام إلى ثلاث واجهات رئيسية للمستخدمين، بالإضافة إلى لوحة الـAdmin/Manager:

## 8.1 Driver PWA

للمندوب.

الشاشات الأساسية:
- Login
- Register
- My Assigned Orders
- Order Details
- My Orders
- Performance
- Profile

---

## 8.2 Trader / Shop PWA

للتجار والمحلات.

الشاشات:
- Login
- Register
- Dashboard
- My Orders (الطلبات الموجهة للمحل)
- Shop Items
- Locations / Branches
- Profile

---

## 8.3 Client Application / PWA

للعميل.

الشاشات:
- Login
- Register
- Home
- Shops
- Shop Details
- Create Delivery
- My Orders
- Order Details
- Saved Addresses
- Profile

---

# 9. Core Business Scenarios

## Scenario A — Trader Creates Delivery (Later Phase)

مؤجل لمرحلة لاحقة؛ في الـMVP الطلبات ينشئها العملاء فقط.

---

## Scenario B — Admin Reviews and Assigns Order

```text
Client creates order
    ↓
Order = CREATED
    ↓
Admin/Manager reviews (approve / reject)
    ↓
Order = AVAILABLE
    ↓
Admin/Manager assigns a Driver
    ↓
Order = ASSIGNED
    ↓
Driver sees it in his assigned orders
    ↓
Picked Up
    ↓
In Delivery
    ↓
Delivered
```

---

## Scenario C — Client Orders From Shop

```text
Client Login
    ↓
Shops
    ↓
Select Shop
    ↓
Select Items
    ↓
Delivery Location
    ↓
Create Order
    ↓
Admin/Manager Review
    ↓
Available
    ↓
Admin/Manager Assigns Driver
    ↓
Delivery
    ↓
Delivered
```

---

## Scenario D — Client Requests Direct Delivery

```text
Client Login
    ↓
Create Delivery
    ↓
Pickup Location
    ↓
Delivery Location
    ↓
Order Details
    ↓
Create Order
    ↓
Admin/Manager Review
    ↓
Available
    ↓
Admin/Manager Assigns Driver
    ↓
Delivery
    ↓
Delivered
```

---

# 10. MVP Scope

## Must Have

### Authentication
- Register (driver, trader, client).
- Login (phone number or username).
- Logout.
- Change password.
- Password recovery via email (email optional at registration, required for recovery).
- Admin/Manager approval of drivers and traders.

### Driver
- My assigned orders and their progress.
- Order details.
- Update progress (picked up, in delivery, delivered).
- My orders.
- Performance.
- Profile.

### Trader
- Shop profile and availability.
- Simple items list.
- Manage locations.
- View and track orders placed to the shop.

### Client
- Browse shops.
- Create delivery.
- Direct pickup-to-delivery request.
- Saved addresses.
- Edit and cancel order (before driver assignment).
- Rate driver.
- My orders.
- Order details.

### Admin / Manager
- Dashboard with time filter.
- Users and approvals.
- Traders / Shops.
- Drivers.
- Orders: review, assign, cancel.
- Set delivery fee and item prices.
- Basic performance overview.

### Cross-cutting
- In-app notifications only.
- Bilingual UI: Arabic (RTL) and English (LTR).

---

# 11. Out of Scope for MVP / Later Phase

لا نضيف في البداية:

- Trader-created orders.
- Full shop catalog (categories, sub-categories, items, sizes, extras, prices).
- Online payment.
- Wallet.
- Complex commission system.
- Advanced financial accounting.
- Multi-level delivery pricing.
- Route optimization.
- Advanced maps/navigation.
- Chat.
- Coupons.
- Loyalty program.
- Advanced analytics.
- Subscription system.
- ERP features.
- Push / SMS notifications.

يمكن إضافتها لاحقًا بعد التأكد من نجاح الـMVP.

---

# 12. Business Rules

1. لا يمكن إسناد أكثر من طلب نشط واحد للمندوب في الـMVP (افتراض لم يؤكده الـPO بعد).
2. الطلب بعد `DELIVERED` لا يمكن تغييره إلى حالة تنفيذية أخرى.
3. الطلب `CANCELLED` لا يمكن إسناده لمندوب.
4. عند إسناد الطلب يتم ربطه بالمندوب؛ لا يوجد قبول أو إرجاع من المندوب.
5. الطلب لا يصبح متاحًا (`AVAILABLE`) إلا بعد مراجعة الـAdmin/Manager، ولا يُسند إلا لمندوب نشط وموافق عليه.
6. العميل يستطيع متابعة طلباته فقط.
7. التاجر يستطيع متابعة الطلبات الموجهة لمحله فقط.
8. الـAdmin والـManager يستطيعان رؤية جميع الطلبات.
9. تغيير كلمة المرور يتم من خلال الحساب المصادق عليه.
10. الأداء الشهري للمندوب يعتمد على الطلبات التي نفذها وتقييماته.
11. الإلغاء: العميل قبل إسناد مندوب فقط، وبعد الإسناد الـAdmin/Manager فقط.
12. تعديل الطلب مسموح للعميل قبل إسناد مندوب فقط.
13. المندوب يرى أرقام هواتف العميل/التاجر بعد إسناد الطلب له فقط.
14. المندوبون والتجار يحتاجون موافقة الـAdmin/Manager؛ العملاء نشطون فورًا.
15. رسوم التوصيل وأسعار المنتجات يحددها الـAdmin/Manager فقط.
16. الـManager له نفس صلاحيات الـAdmin ما عدا إنشاء/تعديل/حذف حسابات الـAdmin.
17. الطلبات ينشئها العملاء فقط في الـMVP.

---

# 13. Simplified Data Model

```text
User (Admin | Manager | Driver | Trader | Client)
 ├── Driver
 ├── Trader
 └── Client

Trader
 ├── Locations
 └── Items

Client
 └── Saved Addresses

Order
 ├── Client (creator)
 ├── Trader (optional)
 ├── Driver (optional, assigned by Admin/Manager)
 ├── Pickup Location
 ├── Delivery Location
 └── Delivery Fee
```

---

# 14. Recommended MVP Priority

## Phase 1 — Foundation
- Authentication.
- User roles (Admin, Manager, Driver, Trader, Client).
- Basic profiles and approvals.

## Phase 2 — Orders
- Create order (client).
- Admin/Manager review.
- Assign order to driver.
- Order lifecycle.

## Phase 3 — Interfaces
- Driver PWA.
- Trader PWA.
- Client PWA.

## Phase 4 — Admin
- Dashboard.
- Users.
- Orders.
- Basic performance.

## Phase 5 — Polish
- Validation.
- In-app notifications.
- Error handling.
- Basic UX improvements.

---

# 15. MVP Success Criteria

الـMVP يعتبر جاهزًا عندما يستطيع:

1. عميل إنشاء طلب.
2. الـAdmin/Manager يراجع الطلب ويجعله متاحًا.
3. الـAdmin/Manager يسند الطلب إلى مندوب.
4. المندوب ينفذ الطلب.
5. الطلب يصل إلى `DELIVERED`.
6. العميل يستطيع متابعة الطلب.
7. الـAdmin/Manager يستطيع رؤية المستخدمين والطلبات.
8. المندوب يستطيع رؤية طلباته المسندة وطلباته السابقة وأداءه.
9. العميل يستطيع إنشاء توصيل مباشر من مكان إلى مكان.
10. الـAdmin/Manager يستطيع الموافقة على المندوبين والتجار.

---

# 16. Product Principle

> **Keep the first version extremely simple.**

نبدأ بدورة واحدة واضحة:

**Create → Review → Available → Assign → Pickup → Delivery → Delivered**

وأي Feature لا تساعد مباشرة في إكمال هذه الدورة يتم تأجيلها إلى ما بعد الـMVP.
