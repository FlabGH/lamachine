<template>
  <div class="metadata-form" :class="{ 'metadata-form--tabs': layout === 'tabs' }">
    <template v-if="layout === 'tabs' && groupedFields.length">
      <div class="tabs" role="tablist" aria-label="Groupes metadata">
        <button
          v-for="group in groupedFields"
          :key="group.name"
          class="tab-button"
          :class="{ 'is-active': group.name === activeGroup }"
          type="button"
          role="tab"
          :aria-selected="group.name === activeGroup"
          @click="activeGroup = group.name"
        >
          {{ group.label }}
        </button>
      </div>

      <section v-if="activeGroupFields" class="metadata-group" role="tabpanel">
        <div v-if="activeGroupFields.primary.length" class="form-grid">
          <MetadataField
            v-for="[name, definition] in activeGroupFields.primary"
            :key="name"
            :name="name"
            :definition="definition"
            :model-value="modelValue[name]"
            @update:model-value="updateField(name, $event)"
          />
        </div>

        <details v-if="activeGroupFields.secondary.length" class="metadata-details">
          <summary>Champs secondaires</summary>
          <div class="form-grid">
            <MetadataField
              v-for="[name, definition] in activeGroupFields.secondary"
              :key="name"
              :name="name"
              :definition="definition"
              :model-value="modelValue[name]"
              @update:model-value="updateField(name, $event)"
            />
          </div>
        </details>

        <details v-if="activeGroupFields.advanced.length" class="metadata-details">
          <summary>Champs avances</summary>
          <div class="form-grid">
            <MetadataField
              v-for="[name, definition] in activeGroupFields.advanced"
              :key="name"
              :name="name"
              :definition="definition"
              :model-value="modelValue[name]"
              @update:model-value="updateField(name, $event)"
            />
          </div>
        </details>
      </section>
    </template>

    <template v-else>
      <section v-for="group in groupedFields" :key="group.name" class="metadata-group">
        <h3 class="metadata-group__title">{{ group.label }}</h3>

        <div v-if="group.primary.length" class="form-grid">
          <MetadataField
            v-for="[name, definition] in group.primary"
            :key="name"
            :name="name"
            :definition="definition"
            :model-value="modelValue[name]"
            @update:model-value="updateField(name, $event)"
          />
        </div>

        <details v-if="group.secondary.length" class="metadata-details">
          <summary>Champs secondaires</summary>
          <div class="form-grid">
            <MetadataField
              v-for="[name, definition] in group.secondary"
              :key="name"
              :name="name"
              :definition="definition"
              :model-value="modelValue[name]"
              @update:model-value="updateField(name, $event)"
            />
          </div>
        </details>

        <details v-if="group.advanced.length" class="metadata-details">
          <summary>Champs avances</summary>
          <div class="form-grid">
            <MetadataField
              v-for="[name, definition] in group.advanced"
              :key="name"
              :name="name"
              :definition="definition"
              :model-value="modelValue[name]"
              @update:model-value="updateField(name, $event)"
            />
          </div>
        </details>
      </section>
    </template>

    <EmptyState
      v-if="groupedFields.length === 0"
      title="Aucune metadata declarable"
      message="Le registre ne contient aucun champ visible dans ce contexte."
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import EmptyState from "../ui/EmptyState.vue";
import MetadataField from "./MetadataField.vue";

const props = defineProps({
  schema: { type: Object, required: true },
  modelValue: { type: Object, required: true },
  context: { type: String, default: "ingestion" },
  layout: { type: String, default: "sections" },
  groups: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:modelValue"]);
const activeGroup = ref("");

const groupLabels = {
  project: "Projet",
  description: "Description",
  classification: "Classification",
  source: "Source",
  retrieval: "Recherche",
  rights: "Droits et acces",
  audit: "Audit",
  technical: "Technique",
};

const editableFields = computed(() =>
  Object.entries(props.schema.fields || {})
    .filter(([, definition]) => {
      const visibleIn = definition.visible_in || ["catalog"];
      if (!visibleIn.includes(props.context)) return false;
      if (props.context === "ingestion") {
        return ["required", "optional"].includes(definition.project_input);
      }
      return definition.project_input !== "forbidden";
    })
    .sort(compareFields),
);

const groupedFields = computed(() => {
  const allowedGroups = new Set(props.groups || []);
  const groups = new Map();
  for (const [name, definition] of editableFields.value) {
    const groupName = definition.presentation_group || "technical";
    if (allowedGroups.size && !allowedGroups.has(groupName)) continue;
    if (!groups.has(groupName)) {
      groups.set(groupName, {
        name: groupName,
        label: groupLabels[groupName] || groupName,
        order: Number.MAX_SAFE_INTEGER,
        primary: [],
        secondary: [],
        advanced: [],
      });
    }
    const group = groups.get(groupName);
    group.order = Math.min(group.order, definition.presentation_order ?? 999);
    const importance = definition.presentation_importance || "secondary";
    group[importance]?.push([name, definition]);
  }
  return Array.from(groups.values()).sort((left, right) => {
    if (left.order !== right.order) return left.order - right.order;
    return left.label.localeCompare(right.label);
  });
});

const activeGroupFields = computed(
  () => groupedFields.value.find((group) => group.name === activeGroup.value) || groupedFields.value[0] || null,
);

watch(
  groupedFields,
  (groups) => {
    if (!groups.length) {
      activeGroup.value = "";
      return;
    }
    if (!groups.some((group) => group.name === activeGroup.value)) {
      activeGroup.value = groups[0].name;
    }
  },
  { immediate: true },
);

function compareFields([leftName, left], [rightName, right]) {
  const leftOrder = left.presentation_order ?? 999;
  const rightOrder = right.presentation_order ?? 999;
  if (leftOrder !== rightOrder) return leftOrder - rightOrder;
  return leftName.localeCompare(rightName);
}

function isEmpty(value) {
  return (
    value === null ||
    value === undefined ||
    value === "" ||
    (Array.isArray(value) && value.length === 0)
  );
}

function updateField(name, value) {
  const next = { ...props.modelValue };
  if (isEmpty(value)) {
    delete next[name];
  } else {
    next[name] = value;
  }
  emit("update:modelValue", next);
}
</script>
