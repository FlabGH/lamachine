<template>
  <div class="view-grid">
    <div class="two-column">
      <AppCard title="Recherche retrieval" subtitle="Prompt libre et preset declaratif">
        <div class="form-grid">
          <div class="field">
            <label for="query">Requete</label>
            <textarea id="query" v-model="query" rows="4" placeholder="Question documentaire" />
          </div>
          <div class="field">
            <label for="indexVersion">Index version</label>
            <select id="indexVersion" v-model="indexVersionId">
              <option value="">Selectionner un index</option>
              <option v-for="item in indexVersions" :key="item.id" :value="item.id">
                {{ item.name }} - {{ item.vector_collection }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="preset">Preset retrieval</label>
            <select id="preset" v-model="preset">
              <option value="">Preset actif projet</option>
              <option v-for="item in presets" :key="item.name" :value="item.name">
                {{ item.name }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="topK">Top K</label>
            <input id="topK" v-model.number="topK" type="number" min="1" max="100" />
          </div>
          <AppButton variant="primary" :disabled="loading || !query || !indexVersionId" @click="runSearch">
            {{ loading ? "Recherche..." : "Rechercher" }}
          </AppButton>
        </div>
      </AppCard>

      <AppCard title="Filtres retrieval">
        <MetadataForm :schema="filterSchema" v-model="filters" context="search" />
      </AppCard>
    </div>

    <ErrorState v-if="error" :message="error" />
    <AppAlert v-if="success" variant="success">{{ success }}</AppAlert>

    <AppCard title="Resultats">
      <EmptyState v-if="!response?.hits?.length" title="Aucun resultat" message="Lancez une recherche ou ajustez les filtres." />
      <DataTable v-else :columns="columns" :rows="response.hits">
        <template #score="{ row }">{{ row.score?.toFixed ? row.score.toFixed(4) : row.score }}</template>
        <template #content="{ row }">{{ row.content.slice(0, 260) }}</template>
      </DataTable>
    </AppCard>

    <AppCard v-if="response" title="Reponse brute">
      <JsonViewer :value="response" />
    </AppCard>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api/client";
import { fetchMetadataSchema, fetchRetrievalPresets } from "../api/catalogs";
import { searchDocuments } from "../api/search";
import MetadataForm from "../components/metadata/MetadataForm.vue";
import AppAlert from "../components/ui/AppAlert.vue";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import DataTable from "../components/ui/DataTable.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import JsonViewer from "../components/ui/JsonViewer.vue";

const query = ref("");
const indexVersionId = ref("");
const preset = ref("");
const topK = ref(5);
const filters = ref({});
const schema = ref({ fields: {} });
const presets = ref([]);
const indexVersions = ref([]);
const response = ref(null);
const loading = ref(false);
const error = ref("");
const success = ref("");
const columns = [
  { key: "rank_final", label: "Rang" },
  { key: "score", label: "Score" },
  { key: "document_id", label: "Document" },
  { key: "chunk_id", label: "Chunk" },
  { key: "content", label: "Extrait" },
];

const filterSchema = computed(() => ({
  fields: Object.fromEntries(
    Object.entries(schema.value.fields || {}).filter(
      ([, definition]) =>
        definition.retrieval_filterable &&
        (definition.visible_in || []).includes("search"),
    ),
  ),
}));

onMounted(async () => {
  const [metadata, presetCatalog, versions] = await Promise.all([
    fetchMetadataSchema(),
    fetchRetrievalPresets(),
    api.get("/index-versions"),
  ]);
  schema.value = metadata;
  presets.value = presetCatalog.items || [];
  indexVersions.value = versions.items || [];
  indexVersionId.value = indexVersions.value[0]?.id || "";
});

async function runSearch() {
  loading.value = true;
  error.value = "";
  success.value = "";
  try {
    response.value = await searchDocuments({
      query: query.value,
      index_version_id: indexVersionId.value,
      top_k: topK.value,
      filters: filters.value,
      preset: preset.value || null,
    });
    success.value = `${response.value.hits.length} resultat(s), run ${response.value.run_id}`;
  } catch (exc) {
    error.value = JSON.stringify(exc?.payload?.detail || exc.message);
  } finally {
    loading.value = false;
  }
}
</script>
