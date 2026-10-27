<script setup>
import { RouterView } from 'vue-router'
import SectionNav from '@/components/SectionNav.vue'

const items = [
  { to: '/client', label: 'client.nav.home', exact: true },
  { to: '/client/orders', label: 'client.nav.orders' },
  { to: '/client/shops', label: 'client.nav.shops' },
  { to: '/client/addresses', label: 'client.nav.addresses' },
]
</script>

<template>
  <section class="layout layout-client" data-testid="layout-client">
    <SectionNav label="client.nav.label" :items="items" />
    <RouterView />
  </section>
</template>
