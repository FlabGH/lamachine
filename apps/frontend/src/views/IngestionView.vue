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
          <div class="field">
            <label for="common-source-code">Source code commun</label>
            <input
              id="common-source-code"
              v-model="common.sourceCode"
              placeholder="Optionnel, sinon derive du nom du fichier"
            />
          </div>
        </div>
      </AppCard>

      <AppCard title="Metadata communes" subtitle="Appliquees au lot, surchargeables fichier par fichier">
        <LoadingState v-if="loadingSchema" />
        <ErrorState v-else-if="schemaError" :message="schemaError" />
        <MetadataForm v-else :schema="editableMetadataSchema" v-model="commonMetadata" />
      </AppCard>
    </div>

    <div class="ingestion-workspace">
      <AppCard title="Fichiers du lot">
        <template #actions>
          <AppButton variant="primary" :disabled="ingesting || readyFiles.length === 0" @click="runBatch">
            {{ ingesting ? "Ingestion..." : "Lancer ingestion" }}
          </AppButton>
        </template>
        <EmptyState v-if="files.length === 0" title="Aucun fichier selectionne" />
        <DataTable v-else :columns="fileColumns" :rows="files">
          <template #focus="{ row }">
            <AppButton :variant="row.id === selectedFileId ? 'primary' : 'default'" @click="selectFile(row.id)">
              Voir
            </AppButton>
          </template>
          <template #include="{ row }">
            <input v-model="row.include" type="checkbox" :disabled="row.status === 'unsupported'" />
          </template>
          <template #sourceCode="{ row }">
            <span>{{ effectiveSourceCode(row) }}</span>
          </template>
          <template #status="{ row }">
            <AppBadge :variant="statusVariant(row)">
              {{ effectiveStatus(row) }}
            </AppBadge>
          </template>
          <template #message="{ row }">
            {{ effectiveMessage(row) }}
          </template>
        </DataTable>
      </AppCard>

      <AppCard
        title="Metadata du fichier"
        :subtitle="selectedFile ? selectedFile.name : 'Selectionner un fichier du lot'"
      >
        <EmptyState v-if="!selectedFile" title="Aucun fichier selectionne" />
        <div v-else class="view-grid">
          <AppAlert v-if="metadataErrors(selectedFile).length" variant="error">
            {{ metadataErrors(selectedFile).join(" ") }}
          </AppAlert>

          <div class="form-grid">
            <div class="field">
              <label for="file-source-code">Source code du fichier</label>
              <input
                id="file-source-code"
                v-model="selectedFile.sourceCode"
                :placeholder="`Fallback: ${selectedFile.fallbackSourceCode}`"
              />
              <p class="field__description">
                Valeur effective: {{ effectiveSourceCode(selectedFile) }}
              </p>
            </div>
          </div>

          <MetadataForm :schema="editableMetadataSchema" v-model="selectedFile.metadata" />

          <div class="actions">
            <AppButton @click="copyCommonMetadataToSelected">Copier les metadata communes</AppButton>
            <AppButton @click="resetSelectedMetadata">Reinitialiser ce fichier</AppButton>
          </div>

          <div class="preview-block">
            <h3 class="section-title">Payload previsualise</h3>
            <JsonViewer :value="previewPayload(selectedFile)" />
          </div>
        </div>
      </AppCard>
    </div>

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
import AppAlert from "../components/ui/AppAlert.vue";
import AppBadge from "../components/ui/AppBadge.vue";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import DataTable from "../components/ui/DataTable.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import JsonViewer from "../components/ui/JsonViewer.vue";
import LoadingState from "../components/ui/LoadingState.vue";

const CONTROLLED_METADATA_FIELDS = new Set([
  "title",
  "source_code",
  "mime_type",
  "filename",
  "author",
  "source_id",
  "document_id",
]);

const files = ref([]);
const results = ref([]);
const selectedFileId = ref(null);
const schema = ref({ fields: {} });
const loadingSchema = ref(true);
const schemaError = ref("");
const ingesting = ref(false);
const commonMetadata = ref({});
const common = reactive({ origin: "", author: "", sourceCode: "" });

const fileColumns = [
  { key: "focus", label: "Fichier" },
  { key: "include", label: "Inclure" },
  { key: "name", label: "Nom" },
  { key: "extension", label: "Extension" },
  { key: "endpoint", label: "Endpoint" },
  { key: "sourceCode", label: "Source code effectif" },
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

const editableMetadataSchema = computed(() => ({
  ...schema.value,
  fields: Object.fromEntries(
    Object.entries(schema.value.fields || {}).filter(
      ([name, definition]) =>
        !CONTROLLED_METADATA_FIELDS.has(name) &&
        ["required", "optional"].includes(definition.project_input),
    ),
  ),
}));

const selectedFile = computed(() => files.value.find((file) => file.id === selectedFileId.value) || null);
const readyFiles = computed(() =>
  files.value.filter((file) => file.include && effectiveStatus(file) === "ready"),
);

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

function slugFromFilename(name) {
  const slug = name
    .replace(/\.[^.]+$/, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
  return slug || "document";
}

function onFilesSelected(event) {
  files.value = Array.from(event.target.files || []).map((file) => {
    const detected = detect(file);
    return {
      id: crypto.randomUUID(),
      file,
      name: file.name,
      extension: file.name.split(".").pop()?.toLowerCase() || "",
      mimeType: file.type || "non expose",
      fallbackSourceCode: slugFromFilename(file.name),
      sourceCode: "",
      metadata: {},
      include: detected.status === "ready",
      endpoint: detected.endpoint,
      status: detected.status,
      message: detected.status === "ready" ? "Pret" : "Format non supporte par les loaders actuels",
    };
  });
  selectedFileId.value = files.value[0]?.id || null;
  results.value = [];
}

function selectFile(fileId) {
  selectedFileId.value = fileId;
}

function effectiveSourceCode(item) {
  return item.sourceCode.trim() || common.sourceCode.trim() || item.fallbackSourceCode || "document";
}

function mergedUserMetadata(item) {
  return sanitizeMetadata({
    ...commonMetadata.value,
    ...item.metadata,
  });
}

function sanitizeMetadata(metadata) {
  return Object.fromEntries(
    Object.entries(metadata || {}).filter(([name, value]) => {
      if (CONTROLLED_METADATA_FIELDS.has(name)) return false;
      if (value === null || value === undefined || value === "") return false;
      if (Array.isArray(value) && value.length === 0) return false;
      return true;
    }),
  );
}

function previewPayload(item) {
  return {
    endpoint: item.endpoint,
    include: item.include,
    form: {
      title: item.name,
      source_code: effectiveSourceCode(item),
      origin: common.origin || null,
      author: common.author || null,
      metadata_json: mergedUserMetadata(item),
    },
  };
}

function metadataErrors(item) {
  const metadata = mergedUserMetadata(item);
  const errors = [];
  for (const [name, definition] of Object.entries(editableMetadataSchema.value.fields || {})) {
    const value = metadata[name];
    if (definition.project_input === "required" && isEmpty(value)) {
      errors.push(`${name} est obligatoire.`);
      continue;
    }
    if (isEmpty(value)) continue;
    const error = validateMetadataValue(name, definition, value);
    if (error) errors.push(error);
  }
  return errors;
}

function validateMetadataValue(name, definition, value) {
  if (definition.type === "enum") {
    if (typeof value !== "string") return `${name} doit etre une chaine.`;
    if (definition.values && !definition.values.includes(value)) {
      return `${name} doit appartenir aux valeurs autorisees.`;
    }
    return "";
  }
  if (definition.type === "list") {
    if (!Array.isArray(value)) return `${name} doit etre une liste.`;
    if (definition.values) {
      const invalid = value.find((item) => !definition.values.includes(item));
      if (invalid) return `${name} contient une valeur non autorisee: ${invalid}.`;
    }
    return "";
  }
  if (definition.type === "boolean" && typeof value !== "boolean") return `${name} doit etre booleen.`;
  if (definition.type === "integer" && !Number.isInteger(value)) return `${name} doit etre entier.`;
  if (definition.type === "number" && typeof value !== "number") return `${name} doit etre numerique.`;
  if (definition.type === "object" && (typeof value !== "object" || Array.isArray(value))) {
    return `${name} doit etre un objet JSON.`;
  }
  return "";
}

function isEmpty(value) {
  return value === null || value === undefined || value === "" || (Array.isArray(value) && value.length === 0);
}

function effectiveStatus(item) {
  if (item.status === "unsupported" || item.status === "ingested" || item.status === "ingestion_error") {
    return item.status;
  }
  if (!item.include) return "exclu";
  if (metadataErrors(item).length) return "metadata_error";
  return "ready";
}

function effectiveMessage(item) {
  const errors = metadataErrors(item);
  if (item.status === "unsupported" || item.status === "ingested" || item.status === "ingestion_error") {
    return item.message;
  }
  if (!item.include) return "Fichier exclu du lot";
  if (errors.length) return errors.join(" ");
  return item.message || "Pret";
}

function statusVariant(item) {
  const status = effectiveStatus(item);
  if (status === "ready" || status === "ingested") return "success";
  if (status === "unsupported" || status === "exclu") return "warning";
  if (status === "metadata_error" || status === "ingestion_error") return "danger";
  return "default";
}

function resetSelectedMetadata() {
  if (!selectedFile.value) return;
  selectedFile.value.metadata = {};
  selectedFile.value.sourceCode = "";
}

function copyCommonMetadataToSelected() {
  if (!selectedFile.value) return;
  selectedFile.value.metadata = { ...commonMetadata.value };
  if (common.sourceCode.trim()) {
    selectedFile.value.sourceCode = common.sourceCode.trim();
  }
}

async function runBatch() {
  ingesting.value = true;
  results.value = [];
  for (const item of readyFiles.value) {
    try {
      const metadata = mergedUserMetadata(item);
      const payload = {
        file: item.file,
        sourceCode: effectiveSourceCode(item),
        metadata,
        origin: common.origin,
        author: common.author,
        title: item.name,
      };
      const response = item.extension === "pdf" ? await ingestPdf(payload) : await ingestText(payload);
      item.status = "ingested";
      item.message = "Ingere";
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
      item.status = "ingestion_error";
      item.message = JSON.stringify(exc?.payload?.detail || exc.message);
      results.value.push({
        id: item.id,
        name: item.name,
        endpoint: item.endpoint,
        status: "error",
        message: item.message,
      });
    }
  }
  ingesting.value = false;
}
</script>
