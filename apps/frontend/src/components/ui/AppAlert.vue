<template>
  <div class="alert" :class="variantClass">
    <slot />
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  variant: { type: String, default: "default" },
});

const variantClass = computed(() => ({
  "alert--error": props.variant === "error",
  "alert--success": props.variant === "success",
}));
</script>
