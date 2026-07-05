<template>
  <div class="alert">
    <strong>{{ title }}</strong>
    <p class="muted">{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: "Aucune donnee" },
  message: { type: String, default: "Aucun element disponible pour cette vue." },
});
</script>
