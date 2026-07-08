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
          <small v-if="!indexVersions.length">
            Aucune index version disponible. Creez une version initiale avant
            d'indexer un document.
          </small>
        </div>
        <AppButton variant="primary" :disabled="!documentId || !indexVersionId || loading" @click="runIndexing">
          {{ loading ? "Indexation..." : "Indexer" }}
        </AppButton>
      </div>
    </AppCard>
    <AppCard v-if="!indexVersions.length" title="Creer une index version initiale">
      <ErrorState v-if="indexVersionError" :message="indexVersionError" />
      <div class="form-grid">
        <div class="field">
          <label for="indexName">Nom</label>
          <input id="indexName" v-model="indexVersionDraft.name" placeholder="Genere si vide" />
        </div>
        <div class="field">
          <label for="embeddingProvider">Embedding provider</label>
          <input id="embeddingProvider" v-model="indexVersionDraft.embedding_provider" />
        </div>
        <div class="field">
          <label for="embeddingModel">Embedding model</label>
          <input id="embeddingModel" v-model="indexVersionDraft.embedding_model" />
        </div>
        <div class="field">
          <label for="embeddingDimension">Dimension</label>
          <input
            id="embeddingDimension"
            v-model.number="indexVersionDraft.embedding_dimension"
            min="1"
            type="number"
          />
        </div>
        <div class="field">
          <label for="vectorCollection">Collection Qdrant</label>
          <input id="vectorCollection" v-model="indexVersionDraft.vector_collection" placeholder="Generee si vide" />
        </div>
        <div class="field">
          <label for="splitStrategy">Strategie de chunking</label>
          <select id="splitStrategy" v-model="indexVersionDraft.split_strategy">
            <option value="generic_window_v1">generic_window_v1</option>
            <option value="generic_recursive_v1">generic_recursive_v1</option>
          </select>
        </div>
        <div class="field">
          <label for="chunkingVersion">Version chunking</label>
          <input id="chunkingVersion" v-model="indexVersionDraft.chunking_version" />
        </div>
        <div class="field">
          <label for="chunkSize">Taille chunk</label>
          <input id="chunkSize" v-model.number="indexVersionDraft.chunk_size" min="1" type="number" />
        </div>
        <div class="field">
          <label for="chunkOverlap">Overlap</label>
          <input id="chunkOverlap" v-model.number="indexVersionDraft.chunk_overlap" min="0" type="number" />
        </div>
        <div class="field">
          <label for="minChunkSize">Taille min</label>
          <input id="minChunkSize" v-model.number="indexVersionDraft.min_chunk_size" min="1" type="number" />
        </div>
        <div class="field">
          <label for="maxChunkSize">Taille max</label>
          <input id="maxChunkSize" v-model.number="indexVersionDraft.max_chunk_size" min="1" type="number" />
        </div>
        <label class="checkbox-field">
          <input v-model="indexVersionDraft.is_active" type="checkbox" />
          Activer cette version
        </label>
        <AppButton variant="secondary" :disabled="creatingIndexVersion" @click="createInitialIndexVersion">
          {{ creatingIndexVersion ? "Creation..." : "Creer l'index version" }}
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
import { createIndexVersion, fetchDocuments, indexDocument } from "../api/documents";
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
const indexVersionError = ref("");
const creatingIndexVersion = ref(false);
const indexVersionDraft = ref({
  name: "",
  embedding_provider: "local",
  embedding_model: "hash-embedding-v1",
  embedding_dimension: 384,
  vector_collection: "",
  split_strategy: "generic_window_v1",
  chunking_version: "generic_window_v1",
  chunk_size: 450,
  chunk_overlap: 80,
  min_chunk_size: 80,
  max_chunk_size: 650,
  is_active: true,
});

onMounted(async () => {
  await loadCatalogs();
});

async function loadCatalogs() {
  const [docs, indexes] = await Promise.all([fetchDocuments(), api.get("/index-versions")]);
  documents.value = docs.items || [];
  indexVersions.value = indexes.items || [];
  if (!indexVersionId.value && indexVersions.value.length) {
    indexVersionId.value = indexVersions.value[0].id;
  }
}

function compactPayload(payload) {
  return Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== "" && value !== null && value !== undefined),
  );
}

async function createInitialIndexVersion() {
  creatingIndexVersion.value = true;
  indexVersionError.value = "";
  try {
    const created = await createIndexVersion(compactPayload(indexVersionDraft.value));
    await loadCatalogs();
    indexVersionId.value = created.id;
  } catch (exc) {
    indexVersionError.value = JSON.stringify(exc?.payload?.detail || exc.message);
  } finally {
    creatingIndexVersion.value = false;
  }
}

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
