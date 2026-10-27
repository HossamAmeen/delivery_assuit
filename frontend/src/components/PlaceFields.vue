<script setup>
import { useI18n } from 'vue-i18n'
import FormField from '@/components/FormField.vue'

// The four place inputs shared by trader locations and client saved addresses.
// `errors` maps field -> message; `idPrefix` keeps ids unique when two forms exist.
const props = defineProps({
  modelValue: { type: Object, required: true },
  errors: { type: Object, default: () => ({}) },
  disabled: { type: Boolean, default: false },
  idPrefix: { type: String, default: 'place' },
})
const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()

const set = (key, value) => emit('update:modelValue', { ...props.modelValue, [key]: value })
</script>

<template>
  <FormField
    :id="`${idPrefix}-name`"
    name="name"
    :label="t('places.name')"
    :model-value="modelValue.name"
    :error="errors.name"
    :disabled="disabled"
    required
    @update:model-value="set('name', $event)"
  />
  <FormField
    :id="`${idPrefix}-address`"
    name="address"
    :label="t('places.address')"
    :model-value="modelValue.address"
    :error="errors.address"
    :disabled="disabled"
    required
    @update:model-value="set('address', $event)"
  />
  <FormField
    :id="`${idPrefix}-latitude`"
    name="latitude"
    :label="t('places.latitude')"
    :hint="t('places.coordinatesHint')"
    :model-value="modelValue.latitude"
    :error="errors.latitude"
    :disabled="disabled"
    inputmode="decimal"
    dir="ltr"
    @update:model-value="set('latitude', $event)"
  />
  <FormField
    :id="`${idPrefix}-longitude`"
    name="longitude"
    :label="t('places.longitude')"
    :model-value="modelValue.longitude"
    :error="errors.longitude"
    :disabled="disabled"
    inputmode="decimal"
    dir="ltr"
    @update:model-value="set('longitude', $event)"
  />
</template>
