<template>
  <div class="two-column">
    <AppCard title="Lancer une indexation">
      <div class="form-grid">
        <div class="field">
          <label for="documentId">Document</label>
          <select id="documentId" v-model="documentId">
            <option value="">Selectionner</option>
            <option v-for="doc in documents" :key="doc.document_id" :value="doc.document_id">{{ doc.title }}</option>
          </select>
        </div>
        <div class="field">
          <label for="indexVersionId">Index version</label>
          <select id="indexVersionId" v-model="indexVersionId">
            <option value="">Selectionner</option>
            <option v-for="index in indexVersions" :key="index.id" :value="index.id">{{ index.name }}</option>
          </select>
        </div>
        <AppButton variant="primary" :disabled="!documentId || !indexVersionId || loading" @click="runIndexing">
          {{ loading ? "Indexation..." : "Indexer" }}
        </AppButton>
      </div>
    </AppCard>
    <AppCard title="Resultat">
      <ErrorState v-if="error" :message="error" />
      <EmptyState v-else-if="!result" title="Aucune indexation lancee" />
      <JsonViewer v-else :value="result" />
    </AppCard>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { api } from "../api/client";
import { fetchDocuments, indexDocument } from "../api/documents";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import JsonViewer from "../components/ui/JsonViewer.vue";

const documents = ref([]);
const indexVersions = ref([]);
const documentId = ref("");
const indexVersionId = ref("");
const result = ref(null);
const error = ref("");
const loading = ref(false);

onMounted(async () => {
  const [docs, indexes] = await Promise.all([fetchDocuments(), api.get("/index-versions")]);
  documents.value = docs.items || [];
  indexVersions.value = indexes.items || [];
});

async function runIndexing() {
  loading.value = true;
  error.value = "";
  try {
    result.value = await indexDocument({
      document_id: documentId.value,
      index_version_id: indexVersionId.value,
    });
  } catch (exc) {
    error.value = JSON.stringify(exc?.payload?.detail || exc.message);
  } finally {
    loading.value = false;
  }
}
</script>
