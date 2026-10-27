<script setup>
import { RouterView } from 'vue-router'
import SectionNav from '@/components/SectionNav.vue'

const items = [
  { to: '/trader', label: 'trader.nav.dashboard', exact: true },
  { to: '/trader/orders', label: 'trader.nav.orders' },
  { to: '/trader/shop', label: 'trader.nav.shop', exact: true },
  { to: '/trader/shop/items', label: 'trader.nav.items' },
  { to: '/trader/locations', label: 'trader.nav.locations' },
]
</script>

<template>
  <section class="layout layout-trader" data-testid="layout-trader">
    <SectionNav label="trader.nav.label" :items="items" />
    <RouterView />
  </section>
</template>
