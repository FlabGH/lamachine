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
      <div v-else class="view-grid">
        <DataTable v-if="active === 'metadata'" :columns="metadataColumns" :rows="metadataRows">
          <template #visible_in="{ row }">{{ row.visible_in.join(", ") }}</template>
          <template #values="{ row }">{{ row.values?.join(", ") || "-" }}</template>
        </DataTable>
        <JsonViewer :value="data" />
      </div>
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
import DataTable from "../components/ui/DataTable.vue";
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
const metadataColumns = [
  { key: "name", label: "Metadata" },
  { key: "presentation_group", label: "Groupe" },
  { key: "presentation_order", label: "Ordre" },
  { key: "presentation_importance", label: "Importance" },
  { key: "presentation_widget", label: "Widget" },
  { key: "visible_in", label: "Visible" },
  { key: "project_input", label: "Saisie" },
  { key: "values", label: "Valeurs" },
];
const metadataRows = computed(() =>
  Object.entries(data.value?.fields || {})
    .map(([name, definition]) => ({ id: name, name, ...definition }))
    .sort((left, right) => {
      if (left.presentation_group !== right.presentation_group) {
        return left.presentation_group.localeCompare(right.presentation_group);
      }
      if (left.presentation_order !== right.presentation_order) {
        return left.presentation_order - right.presentation_order;
      }
      return left.name.localeCompare(right.name);
    }),
);

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
