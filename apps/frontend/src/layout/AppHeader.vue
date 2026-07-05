<template>
  <header class="header">
    <div class="header__title">
      <h1>{{ title }}</h1>
      <p class="header__subtitle">{{ subtitle }}</p>
    </div>
    <slot />
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
});
</script>
