<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import PlaceFields from '@/components/PlaceFields.vue'

// Pick a saved address or type a place. Used for the pickup and delivery sides of an order.
// `errors` maps savedId / name / address / latitude / longitude to a message.
const props = defineProps({
  modelValue: { type: Object, required: true },
  legend: { type: String, required: true },
  addresses: { type: Array, default: () => [] },
  errors: { type: Object, default: () => ({}) },
  disabled: { type: Boolean, default: false },
  idPrefix: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()

const set = (patch) => emit('update:modelValue', { ...props.modelValue, ...patch })
const hasSaved = computed(() => props.addresses.length > 0)
</script>

<template>
  <fieldset class="chooser" :data-test="`${idPrefix}-chooser`">
    <legend>{{ legend }}</legend>

    <div v-if="hasSaved" class="modes">
      <label class="radio">
        <input
          type="radio"
          :name="`${idPrefix}-mode`"
          value="saved"
          :checked="modelValue.mode === 'saved'"
          :disabled="disabled"
          :data-test="`${idPrefix}-mode-saved`"
          @change="set({ mode: 'saved' })"
        />
        {{ t('places.useSaved') }}
      </label>
      <label class="radio">
        <input
          type="radio"
          :name="`${idPrefix}-mode`"
          value="typed"
          :checked="modelValue.mode === 'typed'"
          :disabled="disabled"
          :data-test="`${idPrefix}-mode-typed`"
          @change="set({ mode: 'typed' })"
        />
        {{ t('places.typeNew') }}
      </label>
    </div>

    <div v-if="modelValue.mode === 'saved'" class="field">
      <label :for="`${idPrefix}-saved`">{{ t('places.savedAddress') }}</label>
      <select
        :id="`${idPrefix}-saved`"
        :value="modelValue.savedId"
        :disabled="disabled"
        :aria-invalid="errors.savedId ? 'true' : 'false'"
        :data-test="`${idPrefix}-saved`"
        @change="set({ savedId: $event.target.value })"
      >
        <option value="">{{ t('places.choose') }}</option>
        <option v-for="a in addresses" :key="a.id" :value="String(a.id)">
          {{ a.name }} — {{ a.address }}
        </option>
      </select>
      <p v-if="errors.savedId" class="field-error" role="alert">{{ errors.savedId }}</p>
    </div>

    <PlaceFields
      v-else
      :model-value="modelValue.place"
      :errors="errors"
      :disabled="disabled"
      :id-prefix="idPrefix"
      @update:model-value="set({ place: $event })"
    />
  </fieldset>
</template>

<style scoped>
.chooser {
  display: grid;
  gap: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
}
.modes {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.5rem;
}
.radio {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-block-size: var(--touch-target);
}
.field {
  display: grid;
  gap: 0.375rem;
}
label {
  font-weight: 600;
}
select {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.5rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
}
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
</style>
