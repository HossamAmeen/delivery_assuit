import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import AreaHomeView from '@/views/AreaHomeView.vue'
import RegisterChooserView from '@/views/RegisterChooserView.vue'
import RegisterView from '@/views/RegisterView.vue'
import LoginView from '@/views/LoginView.vue'
import ChangePasswordView from '@/views/ChangePasswordView.vue'
import ProfileView from '@/views/ProfileView.vue'
import ForgotPasswordView from '@/views/ForgotPasswordView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import ApprovalsView from '@/views/ApprovalsView.vue'
import UsersListView from '@/views/UsersListView.vue'
import UserFormView from '@/views/UserFormView.vue'
import ClientEditOrderView from '@/views/ClientEditOrderView.vue'
import ClientOrderView from '@/views/ClientOrderView.vue'
import TraderHomeView from '@/views/TraderHomeView.vue'
import OrderListView from '@/views/OrderListView.vue'
import TraderOrderView from '@/views/TraderOrderView.vue'
import TraderLocationsView from '@/views/TraderLocationsView.vue'
import ClientAddressesView from '@/views/ClientAddressesView.vue'
import ClientShopsView from '@/views/ClientShopsView.vue'
import DriverPerformanceView from '@/views/DriverPerformanceView.vue'
import DriverHistoryView from '@/views/DriverHistoryView.vue'
import DriverOrderView from '@/views/DriverOrderView.vue'
import DriverHomeView from '@/views/DriverHomeView.vue'
import StaffDetailView from '@/views/StaffDetailView.vue'
import AuditView from '@/views/AuditView.vue'
import NotificationsView from '@/views/NotificationsView.vue'
import AdminHomeView from '@/views/AdminHomeView.vue'
import DriverRankingView from '@/views/DriverRankingView.vue'
import StaffListView from '@/views/StaffListView.vue'
import StaffOrderView from '@/views/StaffOrderView.vue'
import OrdersTableView from '@/views/OrdersTableView.vue'
import OrderAssignView from '@/views/OrderAssignView.vue'
import OrderReviewView from '@/views/OrderReviewView.vue'
import DirectDeliveryView from '@/views/DirectDeliveryView.vue'
import OrderFromShopView from '@/views/OrderFromShopView.vue'
import ClientShopView from '@/views/ClientShopView.vue'
import ClientHomeView from '@/views/ClientHomeView.vue'
import TraderShopView from '@/views/TraderShopView.vue'
import TraderItemsView from '@/views/TraderItemsView.vue'
import DriverLayout from '@/layouts/DriverLayout.vue'
import TraderLayout from '@/layouts/TraderLayout.vue'
import ClientLayout from '@/layouts/ClientLayout.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'
import { useAuthStore } from '@/stores/auth'

// meta.public: reachable without a session. meta.roles: roles allowed into the area.
function area(path, component, name, roles) {
  return {
    path,
    component,
    meta: { roles },
    children: [{ path: '', name, component: AreaHomeView }],
  }
}

// The driver area: its own home plus the order screens (Sprint 06).
function driverArea() {
  const base = area('/driver', DriverLayout, 'driver', ['driver'])
  base.children[0].component = DriverHomeView
  base.children.push({ path: 'orders', name: 'driver-orders', component: DriverHistoryView })
  base.children.push({
    path: 'performance',
    name: 'driver-performance',
    component: DriverPerformanceView,
  })
  base.children.push({ path: 'orders/:id(\\d+)', name: 'driver-order', component: DriverOrderView })
  return base
}

// The trader area: dashboard plus the Sprint 04 shop screens.
function traderArea() {
  const base = area('/trader', TraderLayout, 'trader', ['trader'])
  base.children[0].component = TraderHomeView
  base.children.push(
    { path: 'locations', name: 'trader-locations', component: TraderLocationsView },
    { path: 'orders', name: 'trader-orders', component: OrderListView, props: { base: 'trader' } },
    { path: 'orders/:id(\\d+)', name: 'trader-order', component: TraderOrderView },
    { path: 'shop', name: 'trader-shop', component: TraderShopView },
    { path: 'shop/items', name: 'trader-items', component: TraderItemsView },
  )
  return base
}

// The client area has its own home (Sprint 04).
function clientArea() {
  const base = area('/client', ClientLayout, 'client', ['client'])
  base.children[0].component = ClientHomeView
  base.children.push({
    path: 'addresses',
    name: 'client-addresses',
    component: ClientAddressesView,
  })
  base.children.push(
    { path: 'orders', name: 'client-orders', component: OrderListView, props: { base: 'client' } },
    { path: 'orders/:id(\\d+)', name: 'client-order', component: ClientOrderView },
    { path: 'orders/:id(\\d+)/edit', name: 'client-order-edit', component: ClientEditOrderView },
    { path: 'shops', name: 'client-shops', component: ClientShopsView },
    { path: 'direct', name: 'client-direct', component: DirectDeliveryView },
    { path: 'shops/:id(\\d+)', name: 'client-shop', component: ClientShopView },
    { path: 'shops/:id(\\d+)/order', name: 'client-shop-order', component: OrderFromShopView },
  )
  return base
}

// The Admin/Manager area has the dashboard plus the staff screens (Sprint 03).
const ADMIN_ROLES = ['admin', 'manager']
function adminArea() {
  const base = area('/admin', AdminLayout, 'admin', ADMIN_ROLES)
  base.children[0].component = AdminHomeView
  base.children.push(
    { path: 'approvals', name: 'approvals', component: ApprovalsView },
    { path: 'drivers/performance', name: 'driver-ranking', component: DriverRankingView },
    ...['drivers', 'traders', 'clients'].map((kind) => ({
      path: kind,
      name: `staff-${kind}`,
      component: StaffListView,
      props: { kind },
    })),
    ...['drivers', 'traders', 'clients'].map((kind) => ({
      path: `${kind}/:id(\\d+)`,
      name: `staff-${kind.slice(0, -1)}`,
      component: StaffDetailView,
      props: { kind },
    })),
    { path: 'audit', name: 'audit', component: AuditView },
    { path: 'orders', name: 'admin-orders', component: OrdersTableView },
    { path: 'orders/:id(\\d+)', name: 'admin-order', component: StaffOrderView },
    { path: 'orders/review', name: 'order-review', component: OrderReviewView },
    { path: 'orders/assign', name: 'order-assign', component: OrderAssignView },
    { path: 'users', name: 'users', component: UsersListView },
    // 'users/new' comes before 'users/:id' so it is not read as an id.
    { path: 'users/new', name: 'user-create', component: UserFormView },
    { path: 'users/:id(\\d+)', name: 'user-edit', component: UserFormView },
  )
  return base
}

export const routes = [
  { path: '/', name: 'home', component: HomeView, meta: { public: true } },
  // Guest-only: a signed-in user is sent to their own home instead.
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { public: true, guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterChooserView,
    meta: { public: true, guestOnly: true },
  },
  ...['driver', 'trader', 'client'].map((role) => ({
    path: `/register/${role}`,
    name: `register-${role}`,
    component: RegisterView,
    props: { role },
    meta: { public: true, guestOnly: true },
  })),
  // Any signed-in role (no meta.roles): the guard only requires a session.
  { path: '/account/password', name: 'change-password', component: ChangePasswordView },
  { path: '/account/profile', name: 'profile', component: ProfileView },
  // Any signed-in role: everyone has their own notifications.
  { path: '/notifications', name: 'notifications', component: NotificationsView },
  // Public, and not guestOnly: the email link must open even if a session exists.
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: ForgotPasswordView,
    meta: { public: true },
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: ResetPasswordView,
    meta: { public: true },
  },
  driverArea(),
  traderArea(),
  clientArea(),
  adminArea(),
  { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView, meta: { public: true } },
]

// Decision from the store state (never from token text). Returns true to allow, or a redirect.
export function authGuard(to) {
  const auth = useAuthStore()
  const authenticated = auth.isAuthenticated
  if (to.meta.guestOnly && authenticated) return auth.homeRoute
  if (to.meta.public) return true
  if (!authenticated) return { name: 'login' }
  const roles = to.meta.roles
  if (roles && !roles.includes(auth.role)) return auth.homeRoute
  return true
}

export function installGuards(router) {
  router.beforeEach(async (to) => {
    // Wait for the stored session to be restored before deciding (page refresh keeps the user in).
    await useAuthStore().ensureRestored()
    return authGuard(to)
  })
  return router
}

export default installGuards(createRouter({ history: createWebHistory(), routes }))
