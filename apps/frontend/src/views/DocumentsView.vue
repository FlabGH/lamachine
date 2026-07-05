<template>
  <div class="two-column">
    <AppCard title="Documents">
      <template #actions>
        <AppButton @click="loadDocuments">Actualiser</AppButton>
      </template>
      <LoadingState v-if="loading" />
      <ErrorState v-else-if="error" :message="error" />
      <EmptyState v-else-if="documents.length === 0" title="Aucun document" />
      <DataTable v-else :columns="columns" :rows="documents">
        <template #document_id="{ row }">
          <button class="button" type="button" @click="selectDocument(row.document_id)">
            {{ row.document_id }}
          </button>
        </template>
      </DataTable>
    </AppCard>

    <AppCard title="Detail documentaire">
      <EmptyState v-if="!detail" title="Aucun document selectionne" />
      <template v-else>
        <div class="actions">
          <AppButton @click="loadChunks(detail.document_id)">Chunks</AppButton>
          <AppButton @click="loadExtraction(detail.document_id)">Extraction</AppButton>
        </div>
        <JsonViewer :value="{ detail, chunks, extraction }" />
      </template>
    </AppCard>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { fetchDocument, fetchDocumentChunks, fetchDocuments, fetchExtraction } from "../api/documents";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import DataTable from "../components/ui/DataTable.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import JsonViewer from "../components/ui/JsonViewer.vue";
import LoadingState from "../components/ui/LoadingState.vue";

const documents = ref([]);
const detail = ref(null);
const chunks = ref(null);
const extraction = ref(null);
const loading = ref(false);
const error = ref("");
const columns = [
  { key: "document_id", label: "Document" },
  { key: "source_code", label: "Source" },
  { key: "title", label: "Titre" },
  { key: "status", label: "Statut" },
  { key: "chunk_count", label: "Chunks" },
];

onMounted(loadDocuments);

async function loadDocuments() {
  loading.value = true;
  error.value = "";
  try {
    const response = await fetchDocuments();
    documents.value = response.items || [];
  } catch (exc) {
    error.value = exc?.payload?.detail || exc.message;
  } finally {
    loading.value = false;
  }
}

async function selectDocument(documentId) {
  detail.value = await fetchDocument(documentId);
  chunks.value = null;
  extraction.value = null;
}

async function loadChunks(documentId) {
  chunks.value = await fetchDocumentChunks(documentId);
}

async function loadExtraction(documentId) {
  extraction.value = await fetchExtraction(documentId);
}
</script>
