<script setup>
import { computed } from 'vue'

// One labelled input with its hint and error wired for screen readers.
const props = defineProps({
  id: { type: String, required: true },
  label: { type: String, required: true },
  modelValue: { type: [String, Number], default: '' },
  type: { type: String, default: 'text' },
  name: { type: String, default: undefined },
  autocomplete: { type: String, default: undefined },
  inputmode: { type: String, default: undefined },
  dir: { type: String, default: 'auto' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
})
defineEmits(['update:modelValue'])

const describedBy = computed(
  () =>
    [props.error ? `${props.id}-error` : null, props.hint ? `${props.id}-hint` : null]
      .filter(Boolean)
      .join(' ') || undefined,
)
</script>

<template>
  <div class="field">
    <label :for="id">
      {{ label }}<span v-if="required" class="required-mark" aria-hidden="true"> *</span>
    </label>
    <input
      :id="id"
      :value="modelValue"
      :type="type"
      :name="name ?? id"
      :autocomplete="autocomplete"
      :inputmode="inputmode"
      :dir="dir"
      :disabled="disabled"
      :readonly="readonly"
      :required="required"
      :aria-required="required ? 'true' : undefined"
      :aria-invalid="error ? 'true' : 'false'"
      :aria-describedby="describedBy"
      autocapitalize="none"
      spellcheck="false"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <p v-if="hint" :id="`${id}-hint`" class="hint">{{ hint }}</p>
    <p v-if="error" :id="`${id}-error`" class="field-error" role="alert">{{ error }}</p>
  </div>
</template>

<style scoped>
.field {
  display: grid;
  gap: 0.375rem;
}
label {
  font-weight: 600;
}
input {
  font: inherit;
  inline-size: 100%;
  min-inline-size: 0;
  min-block-size: var(--touch-target);
  padding-inline: 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
  color: inherit;
}
input[aria-invalid='true'] {
  border-color: #b42318;
}
input[readonly] {
  background: #f1f3f5;
}
.hint,
.field-error {
  margin: 0;
  font-size: 0.875rem;
}
.hint {
  color: #52606d;
}
.field-error {
  color: #b42318;
}
.required-mark {
  color: #b42318;
}
</style>
