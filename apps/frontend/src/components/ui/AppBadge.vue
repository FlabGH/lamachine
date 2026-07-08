<template>
  <span class="badge" :class="variantClass">
    <slot />
  </span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  variant: { type: String, default: "default" },
});

const variantClass = computed(() => ({
  "badge--success": props.variant === "success",
  "badge--warning": props.variant === "warning",
  "badge--danger": props.variant === "danger",
}));
</script>
