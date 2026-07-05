<template>
  <div class="view-grid">
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" />
    <template v-else>
      <div class="two-column">
        <AppCard title="Sante systeme" subtitle="API, DB et Qdrant">
          <div class="actions">
            <AppBadge :variant="health.api ? 'success' : 'danger'">API</AppBadge>
            <AppBadge :variant="health.db ? 'success' : 'danger'">DB</AppBadge>
            <AppBadge :variant="health.qdrant ? 'success' : 'danger'">Qdrant</AppBadge>
          </div>
          <p class="muted">Preset retrieval actif : {{ summary?.active_retrieval_preset || "non expose" }}</p>
        </AppCard>

        <AppCard title="Projet">
          <p><strong>{{ summary?.project?.project_name || "LaPythie" }}</strong></p>
          <p class="muted">ID : {{ summary?.project?.project_id || "non expose" }}</p>
          <p class="muted">Version config : {{ summary?.project?.config_version || "non expose" }}</p>
        </AppCard>
      </div>

      <AppCard title="Compteurs">
        <DataTable :columns="countColumns" :rows="countRows" />
      </AppCard>

      <div class="two-column">
        <AppCard title="Derniers runs">
          <DataTable :columns="runColumns" :rows="summary?.latest_runs || []" />
          <EmptyState v-if="!summary?.latest_runs?.length" title="Aucun run" />
        </AppCard>
        <AppCard title="Catalogues disponibles">
          <p>Loaders : {{ summary?.loaders?.length || 0 }}</p>
          <p>Enrichisseurs : {{ summary?.enrichers?.length || 0 }}</p>
          <p>Presets retrieval : {{ summary?.retrieval_presets?.length || 0 }}</p>
        </AppCard>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { api } from "../api/client";
import { fetchSystemSummary } from "../api/catalogs";
import AppBadge from "../components/ui/AppBadge.vue";
import AppCard from "../components/ui/AppCard.vue";
import DataTable from "../components/ui/DataTable.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import LoadingState from "../components/ui/LoadingState.vue";

const loading = ref(true);
const error = ref("");
const summary = ref(null);
const health = reactive({ api: false, db: false, qdrant: false });
const countColumns = [{ key: "label", label: "Objet" }, { key: "value", label: "Total" }];
const runColumns = [
  { key: "run_type", label: "Type" },
  { key: "status", label: "Statut" },
  { key: "started_at", label: "Debut" },
];

const countRows = computed(() => {
  const counts = summary.value?.counts || {};
  return Object.entries(counts).map(([label, value]) => ({ id: label, label, value }));
});

onMounted(async () => {
  try {
    const [apiHealth, dbHealth, qdrantHealth, summaryPayload] = await Promise.allSettled([
      api.get("/health"),
      api.get("/health/db"),
      api.get("/health/qdrant"),
      fetchSystemSummary(),
    ]);
    health.api = apiHealth.status === "fulfilled";
    health.db = dbHealth.status === "fulfilled";
    health.qdrant = qdrantHealth.status === "fulfilled";
    if (summaryPayload.status === "fulfilled") {
      summary.value = summaryPayload.value;
    } else {
      throw summaryPayload.reason;
    }
  } catch (exc) {
    error.value = exc?.payload?.detail || exc.message || "Impossible de charger le dashboard.";
  } finally {
    loading.value = false;
  }
});
</script>
