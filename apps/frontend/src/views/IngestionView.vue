<template>
  <div class="view-grid ingestion-view">
    <div class="page-heading">
      <h2>Import de documents</h2>
    </div>

    <AppCard title="Selection des fichiers" subtitle="PDF et TXT sont supportes">
      <div class="form-grid">
        <div class="field">
          <label for="files">Fichiers</label>
          <input id="files" type="file" multiple @change="onFilesSelected" />
        </div>
      </div>
    </AppCard>

    <AppCard title="Fichiers du lot">
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
      title="Metadata du fichier selectionne"
      :subtitle="selectedFile ? selectedFile.name : 'Selectionner un fichier du lot'"
    >
      <LoadingState v-if="loadingSchema" />
      <ErrorState v-else-if="schemaError" :message="schemaError" />
      <EmptyState v-else-if="!selectedFile" title="Aucun fichier selectionne" />
      <div v-else class="view-grid">
        <AppAlert v-if="metadataErrors(selectedFile).length" variant="error">
          {{ metadataErrors(selectedFile).join(" ") }}
        </AppAlert>

        <div class="tabs" role="tablist" aria-label="Metadata du fichier">
          <button
            v-for="tab in fileTabs"
            :key="tab.id"
            class="tab-button"
            :class="{ 'is-active': activeFileTab === tab.id }"
            type="button"
            role="tab"
            :aria-selected="activeFileTab === tab.id"
            @click="activeFileTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <section v-if="activeFileTab === 'source_code'" class="tab-panel" role="tabpanel">
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
        </section>

        <section
          v-else-if="metadataGroupTabs.includes(activeFileTab)"
          class="tab-panel"
          role="tabpanel"
        >
          <MetadataForm
            :schema="editableMetadataSchema"
            v-model="selectedFile.metadata"
            context="ingestion"
            :groups="[activeFileTab]"
          />
        </section>

        <section v-else-if="activeFileTab === 'tools'" class="tab-panel" role="tabpanel">
          <div class="actions">
            <AppButton @click="copyCommonMetadataToSelected">Copier les metadata communes</AppButton>
            <AppButton @click="copySelectedPayload">Copier le payload JSON</AppButton>
            <AppButton @click="resetSelectedMetadata">Reinitialiser les metadata de ce fichier</AppButton>
          </div>
          <div class="preview-block">
            <h3 class="section-title">Payload previsualise</h3>
            <JsonViewer :value="previewPayload(selectedFile)" :show-copy="false" />
          </div>
        </section>
      </div>
    </AppCard>

    <AppCard title="Metadata communes" subtitle="Appliquees au lot, surchargeables fichier par fichier">
      <LoadingState v-if="loadingSchema" />
      <ErrorState v-else-if="schemaError" :message="schemaError" />
      <div v-else class="view-grid">
        <div class="tabs" role="tablist" aria-label="Metadata communes">
          <button
            v-for="tab in commonTabs"
            :key="tab.id"
            class="tab-button"
            :class="{ 'is-active': activeCommonTab === tab.id }"
            type="button"
            role="tab"
            :aria-selected="activeCommonTab === tab.id"
            @click="activeCommonTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>

        <section v-if="activeCommonTab === 'general'" class="tab-panel" role="tabpanel">
          <div class="form-grid">
            <div class="field">
              <label for="origin">Origine commune</label>
              <input id="origin" v-model="common.origin" placeholder="manifest, upload local..." />
            </div>
            <div class="field">
              <label for="author">Auteur commun</label>
              <input id="author" v-model="common.author" placeholder="Optionnel" />
            </div>
          </div>
        </section>

        <section
          v-else-if="metadataGroupTabs.includes(activeCommonTab)"
          class="tab-panel"
          role="tabpanel"
        >
          <MetadataForm
            :schema="editableMetadataSchema"
            v-model="commonMetadata"
            context="ingestion"
            :groups="[activeCommonTab]"
          />
        </section>
      </div>
    </AppCard>

    <AppCard title="Lancer l'ingestion" subtitle="Les fichiers prets et inclus seront traites un par un.">
      <div class="form-grid">
        <label class="checkbox-field">
          <input v-model="autoIndexAfterIngestion" type="checkbox" />
          Indexer automatiquement apres ingestion
        </label>
        <div v-if="autoIndexAfterIngestion" class="field">
          <label for="autoIndexVersion">Index version</label>
          <select id="autoIndexVersion" v-model="autoIndexVersionId">
            <option value="">Selectionner une index version</option>
            <option v-for="index in indexVersions" :key="index.id" :value="index.id">
              {{ index.name }} - {{ index.vector_collection }}
            </option>
          </select>
          <p class="field__description">
            Les chunks sont crees pendant l'indexation. Sans indexation, le document reste en statut ingere/parse.
          </p>
        </div>
        <AppAlert v-if="indexVersionError">
          {{ indexVersionError }}
        </AppAlert>
      </div>
      <div class="actions">
        <AppButton variant="primary" :disabled="ingestionDisabled" @click="runBatch">
          {{ ingesting ? "Ingestion..." : "Lancer ingestion" }}
        </AppButton>
        <span class="muted">{{ readyFiles.length }} fichier(s) pret(s)</span>
      </div>
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
import { api } from "../api/client";
import { fetchMetadataSchema } from "../api/catalogs";
import { indexDocument, ingestPdf, ingestText } from "../api/documents";
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
const indexVersions = ref([]);
const autoIndexAfterIngestion = ref(false);
const autoIndexVersionId = ref("");
const indexVersionError = ref("");
const commonMetadata = ref({});
const common = reactive({ origin: "", author: "" });
const activeFileTab = ref("source_code");
const activeCommonTab = ref("general");

const metadataGroupTabs = ["project", "description", "rights", "source"];
const fileTabs = [
  { id: "source_code", label: "Source code" },
  { id: "project", label: "Projet" },
  { id: "description", label: "Description" },
  { id: "rights", label: "Droits et acces" },
  { id: "source", label: "Source" },
  { id: "tools", label: "Outils" },
];
const commonTabs = [
  { id: "general", label: "General" },
  { id: "project", label: "Projet" },
  { id: "description", label: "Description" },
  { id: "rights", label: "Droits et acces" },
  { id: "source", label: "Source" },
];

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
  { key: "index_status", label: "Indexation" },
  { key: "index_run_id", label: "Run index" },
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
const ingestionDisabled = computed(() =>
  ingesting.value ||
  readyFiles.value.length === 0 ||
  (autoIndexAfterIngestion.value && !autoIndexVersionId.value),
);

onMounted(async () => {
  try {
    schema.value = await fetchMetadataSchema();
  } catch (exc) {
    schemaError.value = exc?.payload?.detail || exc.message || "Configuration ingestion indisponible.";
  } finally {
    loadingSchema.value = false;
  }

  try {
    const versions = await api.get("/index-versions");
    indexVersions.value = versions.items || [];
    autoIndexVersionId.value =
      indexVersions.value.find((index) => index.is_active)?.id ||
      indexVersions.value[0]?.id ||
      "";
    if (!autoIndexVersionId.value) {
      indexVersionError.value = "Aucune index version disponible pour l'indexation automatique.";
    }
  } catch (exc) {
    indexVersionError.value =
      exc?.payload?.detail || exc.message || "Index versions indisponibles pour l'indexation automatique.";
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

function fileSignature(file) {
  return [file.name, file.size, file.lastModified].join(":");
}

function fileToBatchItem(file) {
  const detected = detect(file);
  return {
    id: crypto.randomUUID(),
    signature: fileSignature(file),
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
}

function onFilesSelected(event) {
  const existingSignatures = new Set(files.value.map((file) => file.signature));
  const selectedItems = Array.from(event.target.files || [])
    .filter((file) => {
      const signature = fileSignature(file);
      if (existingSignatures.has(signature)) return false;
      existingSignatures.add(signature);
      return true;
    })
    .map(fileToBatchItem);

  event.target.value = "";
  if (selectedItems.length === 0) return;

  files.value = [...files.value, ...selectedItems];
  selectedFileId.value = selectedItems[0].id;
  activeFileTab.value = "source_code";
  results.value = [];
}

function selectFile(fileId) {
  selectedFileId.value = fileId;
  activeFileTab.value = "source_code";
}

function effectiveSourceCode(item) {
  return item.sourceCode.trim() || item.fallbackSourceCode || "document";
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
  if (
    item.status === "unsupported" ||
    item.status === "ingested" ||
    item.status === "indexed" ||
    item.status === "ingestion_error" ||
    item.status === "indexing_error"
  ) {
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
  if (status === "ready" || status === "ingested" || status === "indexed") return "success";
  if (status === "unsupported" || status === "exclu") return "warning";
  if (status === "metadata_error" || status === "ingestion_error" || status === "indexing_error") return "danger";
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
}

async function copySelectedPayload() {
  if (!selectedFile.value) return;
  await navigator.clipboard.writeText(JSON.stringify(previewPayload(selectedFile.value), null, 2));
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
      item.message = autoIndexAfterIngestion.value
        ? "Document ingere, indexation en cours"
        : "Document ingere, non indexe";
      const result = {
        id: item.id,
        name: item.name,
        endpoint: item.endpoint,
        status: response.status,
        document_id: response.document_id,
        run_id: response.run_id,
        index_status: autoIndexAfterIngestion.value ? "pending" : "non lancee",
        index_run_id: "",
        message: item.message,
      };
      results.value.push(result);
      if (autoIndexAfterIngestion.value) {
        try {
          const indexResponse = await indexDocument({
            document_id: response.document_id,
            index_version_id: autoIndexVersionId.value,
          });
          item.status = "indexed";
          item.message = "Document ingere et indexe";
          result.index_status = indexResponse.status;
          result.index_run_id = indexResponse.id;
          result.message = item.message;
        } catch (exc) {
          item.status = "indexing_error";
          item.message = `Document ingere, erreur indexation: ${JSON.stringify(exc?.payload?.detail || exc.message)}`;
          result.index_status = "error";
          result.message = item.message;
        }
      }
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
