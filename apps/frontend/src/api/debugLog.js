import { reactive } from "vue";

export const apiDebugState = reactive({
  entries: [],
});

export function recordApiCall(entry) {
  apiDebugState.entries.unshift({
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    ...entry,
  });
  if (apiDebugState.entries.length > 30) {
    apiDebugState.entries.pop();
  }
}

export function clearApiLog() {
  apiDebugState.entries.splice(0, apiDebugState.entries.length);
}
