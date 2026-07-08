<template>
  <button class="button" :class="variantClass" :type="type" :disabled="disabled">
    <slot />
  </button>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  variant: { type: String, default: "default" },
  type: { type: String, default: "button" },
  disabled: { type: Boolean, default: false },
});

const variantClass = computed(() => ({
  "button--primary": props.variant === "primary",
  "button--danger": props.variant === "danger",
}));
</script>
