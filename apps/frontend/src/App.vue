<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { apiGet, apiPostForm, apiPostJson } from "./api";

const tabs = [
  { id: "ingestion", label: "Ingestion" },
  { id: "documents", label: "Documents / Chunks" },
  { id: "search", label: "Recherche filtree" },
  { id: "quality", label: "Qualite / Runs / Index" },
];

const metadataFields = [
  "role_documentaire",
  "type_document",
  "theme_tags",
  "data_tags",
  "service_family",
  "service_ids",
  "visibility_scope",
  "organization_id",
  "access_level",
  "language",
];

const primaryMetadata = [
  "source_code",
  "role_documentaire",
  "type_document",
  "theme_tags",
  "data_tags",
  "service_family",
  "service_ids",
  "visibility_scope",
  "organization_id",
  "access_level",
  "language",
  "heading_path",
  "section_level",
  "page_start",
  "page_end",
  "structural_chunking_status",
];

const activeTab = ref("ingestion");
const globalError = ref("");
const globalLoading = ref(false);
const activeIndex = ref(null);
const indexVersions = ref([]);
const capabilities = ref(null);
const metadataCatalog = ref([]);
const sessionRunIds = ref([]);

const ingestion = reactive({
  mode: "pdf",
  title: "",
  source_code: "",
  origin: "",
  author: "",
  text: "",
  file: null,
  metadata: {
    role_documentaire: "",
    type_document: "",
    theme_tags: "",
    data_tags: ["corpus"],
    service_family: "",
    service_ids: "",
    visibility_scope: "public",
    organization_id: "",
    access_level: "open",
    language: "fr",
  },
  result: null,
  extraction: null,
  indexResult: null,
  selectedIndexVersionId: "",
});

const documents = reactive({
  loading: false,
  limit: 20,
  offset: 0,
  total: 0,
  items: [],
  selected: null,
  chunks: [],
  chunksTotal: 0,
  includeContent: false,
  extraction: null,
  extractionPageFrom: "",
  extractionPageTo: "",
});

const search = reactive({
  query: "",
  indexVersionId: "",
  topK: 30,
  rerankTopK: 20,
  filters: {},
  loading: false,
  result: null,
});

const quality = reactive({
  selectedRunId: "",
  run: null,
  hits: [],
  hitsTotal: 0,
});

const implementedFilters = computed(() => {
  return capabilities.value?.implemented_filters ?? [];
});

const metadataCatalogByName = computed(() => {
  return Object.fromEntries(
    metadataCatalog.value.map((item) => [item.metadata, item]),
  );
});

const ingestionMetadataFields = computed(() => {
  return metadataFields.map((field) => ({
    name: field,
    catalog: metadataCatalogByName.value[field] ?? null,
    isList: ["theme_tags", "data_tags", "service_ids"].includes(field),
  }));
});

const selectedDocumentId = computed(() => documents.selected?.document_id ?? "");

function setError(error) {
  globalError.value = error instanceof Error ? error.message : String(error);
}

async function withLoading(task) {
  globalError.value = "";
  globalLoading.value = true;
  try {
    return await task();
  } catch (error) {
    setError(error);
    return null;
  } finally {
    globalLoading.value = false;
  }
}

function splitList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function metadataHelp(field) {
  return metadataCatalogByName.value[field]?.description || "";
}

function buildMetadata() {
  const metadata = {
    title: ingestion.title.trim(),
    source_code: ingestion.source_code.trim(),
  };
  for (const field of metadataFields) {
    const value = ingestion.metadata[field];
    if (["theme_tags", "data_tags", "service_ids"].includes(field)) {
      const values = splitList(value);
      if (values.length) {
        metadata[field] = values;
      }
    } else if (String(value || "").trim()) {
      metadata[field] = String(value).trim();
    }
  }
  return metadata;
}

function appendCommonIngestionFields(formData) {
  formData.append("source_code", ingestion.source_code.trim());
  if (ingestion.origin.trim()) {
    formData.append("origin", ingestion.origin.trim());
  }
  if (ingestion.author.trim()) {
    formData.append("author", ingestion.author.trim());
  }
  formData.append("metadata_json", JSON.stringify(buildMetadata()));
}

function trackRun(runId) {
  if (runId && !sessionRunIds.value.includes(runId)) {
    sessionRunIds.value.unshift(runId);
  }
}

async function loadIndexVersions() {
  const data = await withLoading(() => apiGet("/v1/index-versions?limit=50"));
  if (!data) return;
  indexVersions.value = data.items ?? [];
  if (!ingestion.selectedIndexVersionId && indexVersions.value.length) {
    ingestion.selectedIndexVersionId =
      activeIndex.value?.id ?? indexVersions.value[0].id;
  }
}

async function loadActiveIndex() {
  const data = await withLoading(() => apiGet("/v1/index-versions/active"));
  if (!data) return;
  activeIndex.value = data;
  ingestion.selectedIndexVersionId ||= data.id;
  search.indexVersionId ||= data.id;
}

async function loadCapabilities() {
  const data = await withLoading(() => apiGet("/v1/search/capabilities"));
  if (!data) return;
  capabilities.value = data;
}

async function loadMetadataCatalog() {
  const data = await withLoading(() => apiGet("/v1/metadata/catalog?level=document"));
  if (!data) return;
  metadataCatalog.value = data.items ?? [];
}

async function submitIngestion() {
  await withLoading(async () => {
    const formData = new FormData();
    appendCommonIngestionFields(formData);
    let path = "/documentary/documents/pdf";
    if (ingestion.mode === "pdf") {
      if (!ingestion.file) {
        throw new Error("Selectionner un fichier PDF.");
      }
      formData.append("file", ingestion.file);
    } else {
      path = "/documentary/documents/text";
      formData.append("title", ingestion.title.trim());
      formData.append("text", ingestion.text);
    }

    const data = await apiPostForm(path, formData);
    ingestion.result = data;
    ingestion.extraction = null;
    ingestion.indexResult = null;
    trackRun(data.run_id);
    if (ingestion.mode === "pdf") {
      await loadIngestionExtraction();
    }
  });
}

async function loadIngestionExtraction() {
  if (!ingestion.result?.document_id) return;
  const data = await withLoading(() =>
    apiGet(
      `/v1/documents/${ingestion.result.document_id}/extraction?include_text=false`,
    ),
  );
  if (data) {
    ingestion.extraction = data;
  }
}

async function indexIngestedDocument() {
  if (!ingestion.result?.document_id) {
    setError("Aucun document ingere a indexer.");
    return;
  }
  if (!ingestion.selectedIndexVersionId) {
    setError("Aucune index_version selectionnee.");
    return;
  }
  const data = await withLoading(() =>
    apiPostJson("/documentary/index", {
      document_id: ingestion.result.document_id,
      index_version_id: ingestion.selectedIndexVersionId,
    }),
  );
  if (data) {
    ingestion.indexResult = data;
    trackRun(data.id);
    await loadDocuments();
  }
}

async function loadDocuments() {
  documents.loading = true;
  await withLoading(async () => {
    const data = await apiGet(
      `/v1/documents?limit=${documents.limit}&offset=${documents.offset}`,
    );
    documents.items = data.items ?? [];
    documents.total = data.total ?? 0;
  });
  documents.loading = false;
}

async function selectDocument(document) {
  documents.selected = document;
  documents.chunks = [];
  documents.extraction = null;
  await loadChunks();
}

async function loadChunks() {
  if (!documents.selected) return;
  const data = await withLoading(() =>
    apiGet(
      `/v1/documents/${documents.selected.document_id}/chunks?limit=50&offset=0&include_content=${documents.includeContent}`,
    ),
  );
  if (data) {
    documents.chunks = data.items ?? [];
    documents.chunksTotal = data.total ?? 0;
  }
}

async function loadChunkContent(chunk) {
  const data = await withLoading(() =>
    apiGet(`/v1/chunks/${chunk.chunk_id}?include_content=true`),
  );
  if (!data) return;
  const index = documents.chunks.findIndex((item) => item.chunk_id === chunk.chunk_id);
  if (index >= 0) {
    documents.chunks[index] = data;
  }
}

async function loadDocumentExtraction() {
  if (!documents.selected) return;
  const params = new URLSearchParams();
  params.set("include_text", "true");
  if (documents.extractionPageFrom) {
    params.set("page_from", documents.extractionPageFrom);
  }
  if (documents.extractionPageTo) {
    params.set("page_to", documents.extractionPageTo);
  }
  const data = await withLoading(() =>
    apiGet(`/v1/documents/${documents.selected.document_id}/extraction?${params}`),
  );
  if (data) {
    documents.extraction = data;
  }
}

function buildSearchFilters() {
  const filters = {};
  for (const item of implementedFilters.value) {
    const value = search.filters[item.metadata];
    const values = splitList(value);
    if (values.length) {
      filters[item.metadata] = values;
    }
  }
  return Object.keys(filters).length ? filters : null;
}

async function runSearch() {
  if (!search.query.trim()) {
    setError("Saisir une requete.");
    return;
  }
  if (!search.indexVersionId) {
    setError("Selectionner une index_version.");
    return;
  }
  search.loading = true;
  const data = await withLoading(() =>
    apiPostJson("/v1/search", {
      query: search.query.trim(),
      index_version_id: search.indexVersionId,
      top_k: Number(search.topK),
      rerank_top_k: Number(search.rerankTopK),
      filters: buildSearchFilters(),
    }),
  );
  search.loading = false;
  if (data) {
    search.result = data;
    trackRun(data.run_id);
  }
}

async function loadRun(runId = quality.selectedRunId) {
  if (!runId) {
    setError("Saisir ou selectionner un run_id.");
    return;
  }
  const data = await withLoading(() => apiGet(`/v1/runs/${runId}`));
  if (data) {
    quality.selectedRunId = runId;
    quality.run = data;
    await loadRunHits(runId);
  }
}

async function loadRunHits(runId = quality.selectedRunId) {
  const data = await withLoading(() =>
    apiGet(`/v1/runs/${runId}/retrieval-hits?limit=50&offset=0`),
  );
  if (data) {
    quality.hits = data.items ?? [];
    quality.hitsTotal = data.total ?? 0;
  }
}

function onFileChange(event) {
  ingestion.file = event.target.files?.[0] ?? null;
  if (ingestion.file && !ingestion.title) {
    ingestion.title = ingestion.file.name;
  }
}

function displayMetadata(metadata) {
  if (!metadata) return {};
  return Object.fromEntries(
    Object.entries(metadata).filter(([key]) => primaryMetadata.includes(key)),
  );
}

onMounted(async () => {
  await loadMetadataCatalog();
  await loadCapabilities();
  await loadActiveIndex();
  await loadIndexVersions();
  await loadDocuments();
});
</script>

<template>
  <main class="app-shell">
    <header class="topbar">
      <div>
        <h1>LaMachine POC documentaire</h1>
        <p>Validation ingestion, indexation, consultation et retrieval filtre.</p>
      </div>
      <div class="status-pill" :class="{ muted: !activeIndex }">
        Index actif: {{ activeIndex?.name || "aucun" }}
      </div>
    </header>

    <nav class="tabs" aria-label="Navigation documentaire">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </nav>

    <section v-if="globalError" class="alert error">
      {{ globalError }}
    </section>
    <section v-if="globalLoading" class="alert neutral">
      Chargement API en cours...
    </section>

    <section v-if="activeTab === 'ingestion'" class="panel">
      <div class="panel-heading">
        <h2>Ingestion</h2>
        <p>Ajouter un document PDF ou texte, puis l’indexer explicitement.</p>
      </div>

      <div class="form-grid">
        <label>
          Type
          <select v-model="ingestion.mode">
            <option value="pdf">PDF</option>
            <option value="text">Texte brut</option>
          </select>
        </label>
        <label>
          Titre
          <input v-model="ingestion.title" type="text" placeholder="Titre document" />
        </label>
        <label>
          <span class="field-label">
            source_code
            <span
              v-if="metadataHelp('source_code')"
              class="help-dot"
              :title="metadataHelp('source_code')"
            >?</span>
          </span>
          <input
            v-model="ingestion.source_code"
            type="text"
            placeholder="ps"
            :title="metadataHelp('source_code')"
          />
          <small v-if="metadataHelp('source_code')">{{ metadataHelp("source_code") }}</small>
        </label>
        <label>
          Origin
          <input v-model="ingestion.origin" type="text" placeholder="URL ou origine" />
        </label>
        <label>
          Author
          <input v-model="ingestion.author" type="text" placeholder="Auteur" />
        </label>
        <label v-if="ingestion.mode === 'pdf'">
          PDF
          <input type="file" accept="application/pdf" @change="onFileChange" />
        </label>
      </div>

      <label v-if="ingestion.mode === 'text'" class="full-field">
        Texte
        <textarea v-model="ingestion.text" rows="8" placeholder="Texte a ingerer" />
      </label>

      <h3>Metadata minimales</h3>
      <div class="form-grid">
        <label v-for="field in ingestionMetadataFields" :key="field.name">
          <span class="field-label">
            {{ field.name }}
            <span
              v-if="field.catalog?.description"
              class="help-dot"
              :title="field.catalog.description"
            >?</span>
          </span>
          <select
            v-if="field.catalog?.allowed_values && field.isList"
            v-model="ingestion.metadata[field.name]"
            multiple
            :title="field.catalog.description"
          >
            <option
              v-for="value in field.catalog.allowed_values"
              :key="value"
              :value="value"
            >
              {{ value }}
            </option>
          </select>
          <select
            v-else-if="field.catalog?.allowed_values"
            v-model="ingestion.metadata[field.name]"
            :title="field.catalog.description"
          >
            <option value="">Non renseigne</option>
            <option
              v-for="value in field.catalog.allowed_values"
              :key="value"
              :value="value"
            >
              {{ value }}
            </option>
          </select>
          <input
            v-else
            v-model="ingestion.metadata[field.name]"
            type="text"
            :title="field.catalog?.description"
            :placeholder="field.isList ? 'valeurs separees par virgules' : field.name"
          />
          <small v-if="field.catalog?.description">{{ field.catalog.description }}</small>
        </label>
      </div>

      <div class="actions">
        <button type="button" @click="submitIngestion">Ingerer</button>
        <label>
          Index version
          <select v-model="ingestion.selectedIndexVersionId">
            <option value="">Selectionner</option>
            <option
              v-for="version in indexVersions"
              :key="version.id"
              :value="version.id"
            >
              {{ version.name }} {{ version.is_active ? "(active)" : "" }}
            </option>
          </select>
        </label>
        <button type="button" @click="indexIngestedDocument">
          Indexer le document ingere
        </button>
      </div>

      <div v-if="ingestion.result" class="result-grid">
        <article>
          <h3>Resultat ingestion</h3>
          <pre>{{ ingestion.result }}</pre>
        </article>
        <article v-if="ingestion.extraction">
          <h3>Extraction/OCR</h3>
          <pre>{{ ingestion.extraction.extraction }}</pre>
        </article>
        <article v-if="ingestion.indexResult">
          <h3>Indexation</h3>
          <pre>{{ ingestion.indexResult }}</pre>
        </article>
      </div>
    </section>

    <section v-if="activeTab === 'documents'" class="panel">
      <div class="panel-heading">
        <h2>Documents / Chunks</h2>
        <p>Inspecter les documents, chunks, pages et metadata sans contenu massif par defaut.</p>
      </div>

      <div class="actions">
        <button type="button" @click="loadDocuments">Rafraichir documents</button>
        <span>{{ documents.total }} documents</span>
      </div>

      <div class="split">
        <aside class="list">
          <button
            v-for="document in documents.items"
            :key="document.document_id"
            type="button"
            class="list-item"
            :class="{ selected: selectedDocumentId === document.document_id }"
            @click="selectDocument(document)"
          >
            <strong>{{ document.title }}</strong>
            <span>{{ document.source_code }} · {{ document.chunk_count }} chunks</span>
          </button>
        </aside>

        <div class="detail">
          <p v-if="!documents.selected" class="empty">Selectionner un document.</p>
          <template v-else>
            <h3>{{ documents.selected.title }}</h3>
            <p class="mono">{{ documents.selected.document_id }}</p>
            <pre>{{ displayMetadata(documents.selected.metadata) }}</pre>

            <div class="actions">
              <label class="inline-check">
                <input
                  v-model="documents.includeContent"
                  type="checkbox"
                  @change="loadChunks"
                />
                Afficher contenu chunks
              </label>
              <button type="button" @click="loadChunks">Charger chunks</button>
              <button type="button" @click="loadDocumentExtraction">Charger extraction</button>
              <label>
                Pages de
                <input v-model="documents.extractionPageFrom" type="number" min="1" />
              </label>
              <label>
                a
                <input v-model="documents.extractionPageTo" type="number" min="1" />
              </label>
            </div>

            <section class="cards">
              <article v-for="chunk in documents.chunks" :key="chunk.chunk_id">
                <div class="card-head">
                  <strong>#{{ chunk.chunk_index }}</strong>
                  <span>p. {{ chunk.page_start || "?" }}-{{ chunk.page_end || "?" }}</span>
                </div>
                <p class="mono">{{ chunk.chunk_id }}</p>
                <pre>{{ displayMetadata(chunk.metadata) }}</pre>
                <p v-if="chunk.content" class="chunk-content">{{ chunk.content }}</p>
                <button v-else type="button" @click="loadChunkContent(chunk)">
                  Charger contenu
                </button>
              </article>
            </section>

            <section v-if="documents.extraction">
              <h3>Extraction</h3>
              <pre>{{ documents.extraction.extraction }}</pre>
              <article
                v-for="page in documents.extraction.pages"
                :key="page.page"
                class="page-box"
              >
                <strong>Page {{ page.page }} · {{ page.extraction_source }}</strong>
                <p>{{ page.text }}</p>
              </article>
            </section>
          </template>
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'search'" class="panel">
      <div class="panel-heading">
        <h2>Recherche filtree</h2>
        <p>Tester le retrieval hybride avec les filtres exposes par l’API.</p>
      </div>

      <label class="full-field">
        Requete
        <textarea v-model="search.query" rows="3" placeholder="Question de test" />
      </label>

      <div class="form-grid">
        <label>
          Index version
          <select v-model="search.indexVersionId">
            <option
              v-for="version in indexVersions"
              :key="version.id"
              :value="version.id"
            >
              {{ version.name }} {{ version.is_active ? "(active)" : "" }}
            </option>
          </select>
        </label>
        <label>
          top_k
          <input v-model="search.topK" type="number" min="1" max="100" />
        </label>
        <label>
          rerank_top_k
          <input v-model="search.rerankTopK" type="number" min="1" max="100" />
        </label>
      </div>

      <h3>Filtres supportes</h3>
      <div class="form-grid">
        <label v-for="filter in implementedFilters" :key="filter.metadata">
          {{ filter.metadata }}
          <input
            v-model="search.filters[filter.metadata]"
            type="text"
            placeholder="valeurs separees par virgules"
          />
        </label>
      </div>

      <div class="actions">
        <button type="button" @click="runSearch">Rechercher</button>
        <span v-if="search.result">run_id {{ search.result.run_id }}</span>
      </div>

      <section v-if="search.result" class="cards">
        <article v-for="hit in search.result.hits" :key="hit.chunk_id">
          <div class="card-head">
            <strong>Rang {{ hit.rank_final }}</strong>
            <span>
              dense {{ hit.dense_score ?? "-" }} · lexical {{ hit.lexical_score ?? "-" }}
              · rerank {{ hit.rerank_score ?? "-" }}
            </span>
          </div>
          <p class="mono">chunk {{ hit.chunk_id }}</p>
          <p class="mono">document {{ hit.document_id }}</p>
          <pre>{{ displayMetadata(hit.metadata) }}</pre>
          <p class="chunk-content">{{ hit.content }}</p>
        </article>
      </section>
    </section>

    <section v-if="activeTab === 'quality'" class="panel">
      <div class="panel-heading">
        <h2>Qualite / Runs / Index</h2>
        <p>Verifier index actif, versions, filtres et runs produits pendant la session.</p>
      </div>

      <div class="result-grid">
        <article>
          <h3>Index actif</h3>
          <pre>{{ activeIndex || "Aucun index actif" }}</pre>
        </article>
        <article>
          <h3>Search capabilities</h3>
          <pre>{{ capabilities }}</pre>
        </article>
      </div>

      <h3>Index versions</h3>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Actif</th>
              <th>Collection</th>
              <th>Chunking</th>
              <th>Embedding</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="version in indexVersions" :key="version.id">
              <td>{{ version.name }}</td>
              <td>{{ version.is_active ? "oui" : "non" }}</td>
              <td>{{ version.vector_collection }}</td>
              <td>{{ version.chunking_version }} / {{ version.split_strategy }}</td>
              <td>{{ version.embedding_model }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h3>Runs</h3>
      <div class="actions">
        <select v-model="quality.selectedRunId">
          <option value="">Runs de cette session</option>
          <option v-for="runId in sessionRunIds" :key="runId" :value="runId">
            {{ runId }}
          </option>
        </select>
        <input v-model="quality.selectedRunId" type="text" placeholder="run_id manuel" />
        <button type="button" @click="loadRun()">Charger run</button>
      </div>

      <div v-if="quality.run" class="result-grid">
        <article>
          <h3>Run</h3>
          <pre>{{ quality.run }}</pre>
        </article>
        <article>
          <h3>Retrieval hits ({{ quality.hitsTotal }})</h3>
          <pre>{{ quality.hits }}</pre>
        </article>
      </div>
    </section>
  </main>
</template>

<style>
:root {
  color: #172026;
  background: #f6f8f7;
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
input,
select,
textarea {
  font: inherit;
}

button {
  border: 1px solid #154734;
  background: #154734;
  color: #fff;
  min-height: 36px;
  padding: 0 12px;
  border-radius: 6px;
  cursor: pointer;
}

button:hover {
  background: #0d3325;
}

input,
select,
textarea {
  width: 100%;
  border: 1px solid #bfcbc5;
  border-radius: 6px;
  padding: 8px 10px;
  background: #fff;
  color: #172026;
}

textarea {
  resize: vertical;
}

pre {
  overflow: auto;
  max-height: 360px;
  margin: 8px 0 0;
  padding: 10px;
  border: 1px solid #d5ded9;
  border-radius: 6px;
  background: #f9fbfa;
  font-size: 12px;
  white-space: pre-wrap;
}

.app-shell {
  min-height: 100vh;
  padding: 24px;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.topbar h1 {
  margin: 0;
  font-size: 28px;
}

.topbar p,
.panel-heading p {
  margin: 6px 0 0;
  color: #52625b;
}

.status-pill {
  max-width: 420px;
  border: 1px solid #c6d8cf;
  border-radius: 999px;
  padding: 8px 12px;
  background: #e8f4ee;
  color: #154734;
  font-size: 14px;
}

.status-pill.muted {
  background: #fff4e8;
  color: #7b4a12;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.tabs button {
  background: #fff;
  color: #154734;
}

.tabs button.active {
  background: #154734;
  color: #fff;
}

.panel {
  border: 1px solid #d7e0dc;
  border-radius: 8px;
  background: #fff;
  padding: 18px;
}

.panel-heading {
  margin-bottom: 16px;
}

.panel-heading h2,
h3 {
  margin: 0 0 8px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

label {
  display: grid;
  gap: 6px;
  color: #33423b;
  font-size: 14px;
}

small {
  color: #68776f;
  line-height: 1.35;
}

.field-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.help-dot {
  display: inline-grid;
  width: 18px;
  height: 18px;
  place-items: center;
  border: 1px solid #aab8b1;
  border-radius: 50%;
  color: #52625b;
  font-size: 12px;
  line-height: 1;
}

.full-field {
  display: grid;
  margin-bottom: 16px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 10px;
  margin: 12px 0 16px;
}

.actions label {
  min-width: 260px;
}

.inline-check {
  display: flex;
  width: auto;
  min-width: auto;
  align-items: center;
  grid-template-columns: auto 1fr;
}

.inline-check input {
  width: auto;
}

.alert {
  margin-bottom: 12px;
  border-radius: 6px;
  padding: 10px 12px;
}

.alert.error {
  border: 1px solid #f0b7b7;
  background: #fff0f0;
  color: #8a1f1f;
}

.alert.neutral {
  border: 1px solid #cbd8e7;
  background: #f1f6fc;
  color: #24476b;
}

.result-grid,
.split {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
}

.split {
  grid-template-columns: minmax(260px, 0.35fr) minmax(0, 1fr);
}

.list {
  display: grid;
  align-content: start;
  gap: 8px;
}

.list-item {
  display: grid;
  gap: 4px;
  width: 100%;
  border-color: #d7e0dc;
  background: #fff;
  color: #172026;
  text-align: left;
  padding: 10px;
}

.list-item.selected {
  border-color: #154734;
  background: #edf7f1;
}

.list-item span,
.mono {
  color: #68776f;
  font-size: 12px;
}

.mono {
  overflow-wrap: anywhere;
  font-family: "SFMono-Regular", Consolas, monospace;
}

.cards {
  display: grid;
  gap: 12px;
}

.cards article,
.result-grid article,
.page-box {
  border: 1px solid #d7e0dc;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.chunk-content,
.page-box p {
  max-height: 260px;
  overflow: auto;
  white-space: pre-wrap;
  line-height: 1.45;
}

.table-wrap {
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th,
td {
  border-bottom: 1px solid #d7e0dc;
  padding: 8px;
  text-align: left;
  vertical-align: top;
}

.empty {
  color: #68776f;
}

@media (max-width: 900px) {
  .topbar,
  .result-grid,
  .split {
    grid-template-columns: 1fr;
    display: grid;
  }

  .topbar {
    display: grid;
  }
}
</style>
