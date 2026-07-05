<template>
  <div class="view-grid">
    <div class="two-column">
      <AppCard title="Selection des fichiers" subtitle="PDF et TXT sont supportes">
        <div class="form-grid">
          <div class="field">
            <label for="files">Fichiers</label>
            <input id="files" type="file" multiple @change="onFilesSelected" />
          </div>
          <div class="field">
            <label for="origin">Origine commune</label>
            <input id="origin" v-model="common.origin" placeholder="manifest, upload local..." />
          </div>
          <div class="field">
            <label for="author">Auteur commun</label>
            <input id="author" v-model="common.author" placeholder="Optionnel" />
          </div>
        </div>
      </AppCard>

      <AppCard title="Metadata communes">
        <LoadingState v-if="loadingSchema" />
        <ErrorState v-else-if="schemaError" :message="schemaError" />
        <MetadataForm v-else :schema="schema" v-model="commonMetadata" />
      </AppCard>
    </div>

    <AppCard title="Prevalidation batch">
      <template #actions>
        <AppButton variant="primary" :disabled="ingesting || readyFiles.length === 0" @click="runBatch">
          {{ ingesting ? "Ingestion..." : "Lancer ingestion" }}
        </AppButton>
      </template>
      <EmptyState v-if="files.length === 0" title="Aucun fichier selectionne" />
      <DataTable v-else :columns="fileColumns" :rows="files">
        <template #status="{ row }">
          <AppBadge :variant="row.status === 'ready' ? 'success' : row.status === 'unsupported' ? 'warning' : row.status === 'error' ? 'danger' : 'default'">
            {{ row.status }}
          </AppBadge>
        </template>
        <template #include="{ row }">
          <input v-model="row.include" type="checkbox" :disabled="row.status !== 'ready'" />
        </template>
        <template #sourceCode="{ row }">
          <input v-model="row.sourceCode" :disabled="row.status !== 'ready'" />
        </template>
      </DataTable>
    </AppCard>

    <AppCard title="Suivi ingestion">
      <EmptyState v-if="results.length === 0" title="Aucune ingestion lancee" />
      <DataTable v-else :columns="resultColumns" :rows="results">
        <template #status="{ row }">
          <AppBadge :variant="row.status === 'succeeded' ? 'success' : 'danger'">{{ row.status }}</AppBadge>
        </template>
      </DataTable>
    </AppCard>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { fetchMetadataSchema } from "../api/catalogs";
import { ingestPdf, ingestText } from "../api/documents";
import MetadataForm from "../components/metadata/MetadataForm.vue";
import AppBadge from "../components/ui/AppBadge.vue";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import DataTable from "../components/ui/DataTable.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import LoadingState from "../components/ui/LoadingState.vue";

const files = ref([]);
const results = ref([]);
const schema = ref({ fields: {} });
const loadingSchema = ref(true);
const schemaError = ref("");
const ingesting = ref(false);
const commonMetadata = ref({});
const common = reactive({ origin: "", author: "" });

const fileColumns = [
  { key: "include", label: "Inclure" },
  { key: "name", label: "Fichier" },
  { key: "extension", label: "Extension" },
  { key: "mimeType", label: "MIME" },
  { key: "endpoint", label: "Endpoint" },
  { key: "sourceCode", label: "Source code" },
  { key: "status", label: "Statut" },
  { key: "message", label: "Message" },
];
const resultColumns = [
  { key: "name", label: "Fichier" },
  { key: "status", label: "Statut" },
  { key: "document_id", label: "Document" },
  { key: "run_id", label: "Run" },
  { key: "endpoint", label: "Endpoint" },
  { key: "message", label: "Message" },
];
const readyFiles = computed(() => files.value.filter((file) => file.include && file.status === "ready"));

onMounted(async () => {
  try {
    schema.value = await fetchMetadataSchema();
  } catch (exc) {
    schemaError.value = exc?.payload?.detail || exc.message || "Schema metadata indisponible.";
  } finally {
    loadingSchema.value = false;
  }
});

function detect(file) {
  const extension = file.name.split(".").pop()?.toLowerCase() || "";
  if (extension === "pdf") return { endpoint: "/api/documents/pdf", status: "ready" };
  if (extension === "txt") return { endpoint: "/api/documents/text", status: "ready" };
  return { endpoint: "non supporte", status: "unsupported" };
}

function onFilesSelected(event) {
  files.value = Array.from(event.target.files || []).map((file) => {
    const detected = detect(file);
    const sourceCode = file.name.replace(/\.[^.]+$/, "").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
    return {
      id: crypto.randomUUID(),
      file,
      name: file.name,
      extension: file.name.split(".").pop()?.toLowerCase() || "",
      mimeType: file.type || "non expose",
      sourceCode,
      include: detected.status === "ready",
      endpoint: detected.endpoint,
      status: detected.status,
      message: detected.status === "ready" ? "Pret" : "Format non supporte par les loaders actuels",
    };
  });
}

async function runBatch() {
  ingesting.value = true;
  results.value = [];
  for (const item of readyFiles.value) {
    try {
      const metadata = { ...commonMetadata.value, title: item.name };
      const payload = {
        file: item.file,
        sourceCode: item.sourceCode,
        metadata,
        origin: common.origin,
        author: common.author,
        title: item.name,
      };
      const response = item.extension === "pdf" ? await ingestPdf(payload) : await ingestText(payload);
      results.value.push({
        id: item.id,
        name: item.name,
        endpoint: item.endpoint,
        status: response.status,
        document_id: response.document_id,
        run_id: response.run_id,
        message: "OK",
      });
    } catch (exc) {
      results.value.push({
        id: item.id,
        name: item.name,
        endpoint: item.endpoint,
        status: "error",
        message: JSON.stringify(exc?.payload?.detail || exc.message),
      });
    }
  }
  ingesting.value = false;
}
</script>
