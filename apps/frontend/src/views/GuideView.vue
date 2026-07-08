<template>
  <div class="view-grid">
    <AppCard title="Guide utilisateur" subtitle="Version integree au frontend">
      <template #actions>
        <a class="button" href="/ui/guide/lapythie_guide_utilisateur_v260701.md" target="_blank" rel="noreferrer">
          Version brute
        </a>
      </template>
      <div class="field">
        <label for="guideSearch">Recherche dans le guide</label>
        <input id="guideSearch" v-model="search" placeholder="metadata, chunking, retrieval..." />
      </div>
    </AppCard>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <AppCard v-else>
      <pre class="guide-text">{{ filteredGuide }}</pre>
    </AppCard>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import AppCard from "../components/ui/AppCard.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import LoadingState from "../components/ui/LoadingState.vue";

const guide = ref("");
const search = ref("");
const loading = ref(true);
const error = ref("");

const filteredGuide = computed(() => {
  const term = search.value.trim().toLowerCase();
  if (!term) return guide.value;
  return guide.value
    .split("\n")
    .filter((line) => line.toLowerCase().includes(term) || line.startsWith("#"))
    .join("\n");
});

onMounted(async () => {
  try {
    const response = await fetch("/ui/guide/lapythie_guide_utilisateur_v260701.md");
    guide.value = await response.text();
  } catch (exc) {
    error.value = exc.message || "Guide indisponible.";
  } finally {
    loading.value = false;
  }
});
</script>
