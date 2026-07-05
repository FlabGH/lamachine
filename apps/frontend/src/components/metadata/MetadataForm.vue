<template>
  <div class="form-grid">
    <MetadataField
      v-for="[name, definition] in editableFields"
      :key="name"
      :name="name"
      :definition="definition"
      :model-value="modelValue[name]"
      @update:model-value="updateField(name, $event)"
    />
    <EmptyState
      v-if="editableFields.length === 0"
      title="Aucune metadata declarable"
      message="Le registre ne contient aucun champ project_input required ou optional."
    />
  </div>
</template>

<script setup>
import { computed } from "vue";
import EmptyState from "../ui/EmptyState.vue";
import MetadataField from "./MetadataField.vue";

const props = defineProps({
  schema: { type: Object, required: true },
  modelValue: { type: Object, required: true },
});

const emit = defineEmits(["update:modelValue"]);

const editableFields = computed(() =>
  Object.entries(props.schema.fields || {}).filter(([, definition]) =>
    ["required", "optional"].includes(definition.project_input),
  ),
);

function updateField(name, value) {
  const next = { ...props.modelValue };
  if (value === null || value === undefined || value === "") {
    delete next[name];
  } else {
    next[name] = value;
  }
  emit("update:modelValue", next);
}
</script>
