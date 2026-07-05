<template>
  <AppAlert variant="error">
    <strong>{{ title }}</strong>
    <p>{{ message }}</p>
  </AppAlert>
</template>

<script setup>
import AppAlert from "./AppAlert.vue";

defineProps({
  title: { type: String, default: "Erreur" },
  message: { type: String, default: "Une erreur est survenue." },
});
</script>
