<script setup>
import { RouterView } from 'vue-router'
import SectionNav from '@/components/SectionNav.vue'

const items = [
  { to: '/admin', label: 'admin.nav.dashboard', exact: true },
  { to: '/admin/approvals', label: 'admin.nav.approvals' },
  { to: '/admin/orders', label: 'admin.nav.allOrders', exact: true },
  { to: '/admin/orders/review', label: 'admin.nav.orders' },
  { to: '/admin/orders/assign', label: 'admin.nav.assign' },
  { to: '/admin/drivers', label: 'admin.nav.drivers' },
  { to: '/admin/traders', label: 'admin.nav.traders' },
  { to: '/admin/clients', label: 'admin.nav.clients' },
  { to: '/admin/users', label: 'admin.nav.users' },
  { to: '/admin/audit', label: 'admin.nav.audit' },
]
</script>

<template>
  <section class="layout layout-admin" data-testid="layout-admin">
    <SectionNav label="admin.nav.label" :items="items" />
    <RouterView />
  </section>
</template>
