<template>
  <div class="view-grid">
    <div class="actions">
      <AppButton v-if="showCopy" @click="copyJson">Copier JSON</AppButton>
    </div>
    <pre class="json-viewer">{{ formatted }}</pre>
  </div>
</template>

<script setup>
import { computed } from "vue";
import AppButton from "./AppButton.vue";

const props = defineProps({
  value: { type: null, required: true },
  showCopy: { type: Boolean, default: true },
});

const formatted = computed(() => JSON.stringify(props.value, null, 2));

async function copyJson() {
  await navigator.clipboard.writeText(formatted.value);
}
</script>
