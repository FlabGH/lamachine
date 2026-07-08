<template>
  <div class="view-grid">
    <div class="two-column">
      <AppCard title="Parametres preview">
        <div class="form-grid">
          <div class="field">
            <label for="documentId">Document</label>
            <select id="documentId" v-model="documentId">
              <option value="">Selectionner</option>
              <option v-for="item in documents" :key="item.document_id" :value="item.document_id">
                {{ item.title }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="strategy">Strategie</label>
            <select id="strategy" v-model="payload.split_strategy">
              <option value="">Par defaut index</option>
              <option v-for="item in strategies" :key="item.name" :value="item.name">
                {{ item.name }}
              </option>
            </select>
          </div>
          <div class="field">
            <label for="chunkSize">Chunk size</label>
            <input id="chunkSize" v-model.number="payload.chunk_size" type="number" />
          </div>
          <div class="field">
            <label for="chunkOverlap">Chunk overlap</label>
            <input id="chunkOverlap" v-model.number="payload.chunk_overlap" type="number" />
          </div>
          <AppButton variant="primary" :disabled="!documentId || loading" @click="runPreview">Previsualiser</AppButton>
        </div>
      </AppCard>
      <AppCard title="Strategie disponibles">
        <JsonViewer :value="strategies" />
      </AppCard>
    </div>
    <ErrorState v-if="error" :message="error" />
    <AppCard title="Chunks previsualises">
      <EmptyState v-if="!preview?.chunks?.length" title="Aucun preview" />
      <DataTable v-else :columns="columns" :rows="preview.chunks">
        <template #content="{ row }">{{ row.content.slice(0, 220) }}</template>
      </DataTable>
    </AppCard>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { fetchChunkingStrategies } from "../api/catalogs";
import { fetchDocuments, previewChunking } from "../api/documents";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import DataTable from "../components/ui/DataTable.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import JsonViewer from "../components/ui/JsonViewer.vue";

const documents = ref([]);
const strategies = ref([]);
const documentId = ref("");
const preview = ref(null);
const loading = ref(false);
const error = ref("");
const payload = reactive({ split_strategy: "", chunk_size: 450, chunk_overlap: 80 });
const columns = [
  { key: "chunk_index", label: "Ordre" },
  { key: "token_count", label: "Tokens" },
  { key: "section_title", label: "Section" },
  { key: "content", label: "Extrait" },
];

onMounted(async () => {
  const [docs, strategyCatalog] = await Promise.all([fetchDocuments(), fetchChunkingStrategies()]);
  documents.value = docs.items || [];
  strategies.value = strategyCatalog.items || [];
});

async function runPreview() {
  loading.value = true;
  error.value = "";
  try {
    preview.value = await previewChunking(documentId.value, {
      ...payload,
      split_strategy: payload.split_strategy || null,
    });
  } catch (exc) {
    error.value = JSON.stringify(exc?.payload?.detail || exc.message);
  } finally {
    loading.value = false;
  }
}
</script>
