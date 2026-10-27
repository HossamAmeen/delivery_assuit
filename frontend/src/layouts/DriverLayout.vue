<script setup>
import { RouterView } from 'vue-router'
import SectionNav from '@/components/SectionNav.vue'

const items = [
  { to: '/driver', label: 'driver.nav.home', exact: true },
  { to: '/driver/orders', label: 'driver.nav.orders', exact: true },
  { to: '/driver/performance', label: 'driver.nav.performance' },
  { to: '/account/profile', label: 'driver.nav.profile' },
]
</script>

<template>
  <section class="layout layout-driver" data-testid="layout-driver">
    <SectionNav label="driver.nav.label" :items="items" />
    <RouterView />
  </section>
</template>
