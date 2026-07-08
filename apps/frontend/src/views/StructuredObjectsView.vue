<template>
  <div class="two-column">
    <AppCard title="Objets structures">
      <template #actions>
        <AppButton @click="loadObjects">Actualiser</AppButton>
      </template>
      <EmptyState v-if="objects.length === 0" title="Aucun objet structure" message="La production automatique reste en construction." />
      <DataTable v-else :columns="columns" :rows="objects">
        <template #object_id="{ row }">
          <button class="button" type="button" @click="selectObject(row.object_id)">{{ row.object_id }}</button>
        </template>
      </DataTable>
    </AppCard>
    <AppCard title="Detail / recherche">
      <div class="form-grid">
        <div class="field">
          <label for="objectQuery">Recherche objets</label>
          <input id="objectQuery" v-model="query" placeholder="recommendations, risks..." />
        </div>
        <div class="field">
          <label for="objectIndex">Index version</label>
          <input id="objectIndex" v-model="indexVersionId" placeholder="UUID index version" />
        </div>
        <AppButton :disabled="!query || !indexVersionId" @click="runSearch">Rechercher objets</AppButton>
      </div>
      <JsonViewer v-if="detail" :value="detail" />
      <JsonViewer v-if="searchResult" :value="searchResult" />
    </AppCard>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { searchStructuredObjects } from "../api/search";
import { fetchStructuredObject, fetchStructuredObjects } from "../api/structuredObjects";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import DataTable from "../components/ui/DataTable.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import JsonViewer from "../components/ui/JsonViewer.vue";

const objects = ref([]);
const detail = ref(null);
const searchResult = ref(null);
const query = ref("");
const indexVersionId = ref("");
const columns = [
  { key: "object_id", label: "Objet" },
  { key: "object_type", label: "Type" },
  { key: "title", label: "Titre" },
  { key: "confidence", label: "Confiance" },
];

onMounted(loadObjects);

async function loadObjects() {
  const response = await fetchStructuredObjects();
  objects.value = response.items || [];
}

async function selectObject(objectId) {
  detail.value = await fetchStructuredObject(objectId);
}

async function runSearch() {
  searchResult.value = await searchStructuredObjects({
    query: query.value,
    index_version_id: indexVersionId.value,
    top_k: 10,
  });
}
</script>
