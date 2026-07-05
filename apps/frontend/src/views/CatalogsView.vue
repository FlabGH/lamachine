<template>
  <div class="view-grid">
    <AppCard title="Catalogues et capacites">
      <div class="actions">
        <AppButton v-for="item in catalogItems" :key="item.id" @click="active = item.id">
          {{ item.label }}
        </AppButton>
      </div>
    </AppCard>

    <AppCard :title="current.label">
      <template #actions>
        <AppButton @click="loadCatalog">Actualiser</AppButton>
      </template>
      <LoadingState v-if="loading" />
      <ErrorState v-else-if="error" :message="error" />
      <JsonViewer v-else :value="data" />
    </AppCard>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import {
  fetchChunkingStrategies,
  fetchEnrichers,
  fetchLoaders,
  fetchMetadataSchema,
  fetchProjectConfig,
  fetchRetrievalPresets,
  fetchSearchCapabilities,
} from "../api/catalogs";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import JsonViewer from "../components/ui/JsonViewer.vue";
import LoadingState from "../components/ui/LoadingState.vue";

const catalogItems = [
  { id: "metadata", label: "Metadata", loader: fetchMetadataSchema },
  { id: "chunking", label: "Chunking", loader: fetchChunkingStrategies },
  { id: "loaders", label: "Loaders", loader: fetchLoaders },
  { id: "enrichers", label: "Enrichers", loader: fetchEnrichers },
  { id: "presets", label: "Presets retrieval", loader: fetchRetrievalPresets },
  { id: "capabilities", label: "Capacites recherche", loader: fetchSearchCapabilities },
  { id: "project", label: "Projet", loader: fetchProjectConfig },
];
const active = ref("metadata");
const data = ref(null);
const loading = ref(false);
const error = ref("");
const current = computed(() => catalogItems.find((item) => item.id === active.value) || catalogItems[0]);

onMounted(loadCatalog);

async function loadCatalog() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await current.value.loader();
  } catch (exc) {
    error.value = exc?.payload?.detail || exc.message;
  } finally {
    loading.value = false;
  }
}
</script>
