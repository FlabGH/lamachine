<template>
  <div class="two-column">
    <AppCard title="Runs">
      <template #actions>
        <AppButton @click="loadRuns">Actualiser</AppButton>
      </template>
      <LoadingState v-if="loading" />
      <ErrorState v-else-if="error" :message="error" />
      <EmptyState v-else-if="runs.length === 0" title="Aucun run" />
      <DataTable v-else :columns="columns" :rows="runs">
        <template #run_id="{ row }">
          <button class="button" type="button" @click="selectRun(row.run_id)">
            {{ row.run_id }}
          </button>
        </template>
      </DataTable>
    </AppCard>

    <AppCard title="Detail du run">
      <EmptyState v-if="!selectedRun" title="Aucun run selectionne" />
      <template v-else>
        <JsonViewer :value="selectedRun" />
        <AppButton v-if="selectedRun.run_type === 'retrieval'" @click="loadHits(selectedRun.run_id)">
          Charger retrieval hits
        </AppButton>
        <JsonViewer v-if="hits" :value="hits" />
      </template>
    </AppCard>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { fetchRetrievalHits, fetchRun, fetchRuns } from "../api/runs";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import DataTable from "../components/ui/DataTable.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import JsonViewer from "../components/ui/JsonViewer.vue";
import LoadingState from "../components/ui/LoadingState.vue";

const runs = ref([]);
const selectedRun = ref(null);
const hits = ref(null);
const loading = ref(false);
const error = ref("");
const columns = [
  { key: "run_id", label: "Run" },
  { key: "run_type", label: "Type" },
  { key: "status", label: "Statut" },
  { key: "started_at", label: "Debut" },
];

onMounted(loadRuns);

async function loadRuns() {
  loading.value = true;
  error.value = "";
  try {
    const response = await fetchRuns();
    runs.value = response.items || [];
  } catch (exc) {
    error.value = exc?.payload?.detail || exc.message;
  } finally {
    loading.value = false;
  }
}

async function selectRun(runId) {
  selectedRun.value = await fetchRun(runId);
  hits.value = null;
}

async function loadHits(runId) {
  hits.value = await fetchRetrievalHits(runId);
}
</script>
