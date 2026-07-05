<template>
  <div class="view-grid">
    <AppCard title="Journal debug API" subtitle="Derniers appels faits par le frontend">
      <template #actions>
        <AppButton @click="clearApiLog">Vider</AppButton>
      </template>
      <EmptyState v-if="apiDebugState.entries.length === 0" title="Aucun appel API" />
      <DataTable v-else :columns="columns" :rows="apiDebugState.entries">
        <template #url="{ row }">{{ row.method }} {{ row.url }}</template>
        <template #response="{ row }">
          <AppButton @click="copy(row.response)">Copier reponse</AppButton>
        </template>
        <template #request="{ row }">
          <AppButton @click="copy(row.request)">Copier payload</AppButton>
        </template>
      </DataTable>
    </AppCard>
    <AppCard v-if="apiDebugState.entries[0]" title="Dernier appel">
      <JsonViewer :value="apiDebugState.entries[0]" />
    </AppCard>
  </div>
</template>

<script setup>
import { apiDebugState, clearApiLog } from "../api/debugLog";
import AppButton from "../components/ui/AppButton.vue";
import AppCard from "../components/ui/AppCard.vue";
import DataTable from "../components/ui/DataTable.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import JsonViewer from "../components/ui/JsonViewer.vue";

const columns = [
  { key: "timestamp", label: "Date" },
  { key: "url", label: "URL" },
  { key: "status", label: "Statut" },
  { key: "durationMs", label: "ms" },
  { key: "request", label: "Payload" },
  { key: "response", label: "Reponse" },
];

async function copy(value) {
  await navigator.clipboard.writeText(typeof value === "string" ? value : JSON.stringify(value, null, 2));
}
</script>
