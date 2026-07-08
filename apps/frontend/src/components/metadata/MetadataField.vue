<template>
  <div class="field">
    <label :for="fieldId">
      {{ name }}
      <span v-if="isRequiredInput" class="muted">(obligatoire)</span>
    </label>
    <p v-if="description" class="field__description">
      {{ description }}
    </p>

    <select
      v-if="definition.type === 'enum' && definition.values"
      :id="fieldId"
      :value="modelValue ?? ''"
      @input="emitValue($event.target.value || null)"
    >
      <option value="">Non renseigne</option>
      <option v-for="value in definition.values" :key="value" :value="value">
        {{ value }}
      </option>
    </select>

    <select
      v-else-if="isListWidget && definition.values"
      :id="fieldId"
      multiple
      :value="arrayValue"
      @change="emitSelectedOptions($event.target.selectedOptions)"
    >
      <option v-for="value in definition.values" :key="value" :value="value">
        {{ value }}
      </option>
    </select>

    <select
      v-else-if="definition.type === 'boolean'"
      :id="fieldId"
      :value="modelValue === null || modelValue === undefined ? '' : String(modelValue)"
      @input="emitValue($event.target.value === '' ? null : $event.target.value === 'true')"
    >
      <option value="">Non renseigne</option>
      <option value="true">true</option>
      <option value="false">false</option>
    </select>

    <textarea
      v-else-if="widget === 'textarea'"
      :id="fieldId"
      :value="inputValue"
      rows="4"
      :placeholder="placeholder"
      @input="emitText($event.target.value)"
    />

    <textarea
      v-else-if="definition.type === 'object'"
      :id="fieldId"
      :value="objectText"
      rows="4"
      placeholder='{"key": "value"}'
      @input="emitRaw($event.target.value)"
    />

    <input
      v-else
      :id="fieldId"
      :type="inputType"
      :value="inputValue"
      :placeholder="placeholder"
      @input="emitText($event.target.value)"
    />

    <p v-if="isListWidget" class="field__description">
      {{ definition.values ? "Selection multiple autorisee." : "Saisir des tags separes par des virgules." }}
    </p>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  name: { type: String, required: true },
  definition: { type: Object, required: true },
  context: { type: String, default: "ingestion" },
  modelValue: { type: null, default: null },
});

const emit = defineEmits(["update:modelValue"]);
const fieldId = computed(() => `metadata-${props.name}`);
const widget = computed(() => props.definition.presentation_widget || "");
const isSearchContext = computed(() => props.context === "search");
const isRequiredInput = computed(() =>
  props.definition.project_input === "required" && !isSearchContext.value,
);
const description = computed(() => {
  if (isSearchContext.value && props.name === "source_code") {
    return "Filtre optionnel : limite la recherche à une source documentaire.";
  }
  return props.definition.description || "";
});
const isListWidget = computed(() =>
  props.definition.type === "list" &&
  ["tags", "multiselect"].includes(widget.value),
);
const inputType = computed(() => {
  if (props.definition.type === "date") return "date";
  if (props.definition.type === "datetime") return "datetime-local";
  if (["number", "integer"].includes(props.definition.type)) return "number";
  return "text";
});
const placeholder = computed(() => {
  if (props.definition.type === "list") return "valeur1, valeur2";
  if (isSearchContext.value) return "Filtre optionnel";
  return props.definition.project_input === "required" ? "Valeur requise" : "Optionnel";
});
const inputValue = computed(() => {
  if (Array.isArray(props.modelValue)) return props.modelValue.join(", ");
  return props.modelValue ?? "";
});
const arrayValue = computed(() => (Array.isArray(props.modelValue) ? props.modelValue : []));
const objectText = computed(() => {
  if (!props.modelValue) return "";
  if (typeof props.modelValue === "string") return props.modelValue;
  return JSON.stringify(props.modelValue, null, 2);
});

function emitValue(value) {
  emit("update:modelValue", value);
}

function emitRaw(value) {
  if (!value.trim()) {
    emitValue(null);
    return;
  }
  try {
    emitValue(JSON.parse(value));
  } catch {
    emitValue(value);
  }
}

function emitSelectedOptions(options) {
  emitValue(Array.from(options).map((option) => option.value));
}

function emitText(value) {
  if (!value.trim()) {
    emitValue(null);
    return;
  }
  if (props.definition.type === "list") {
    emitValue(value.split(",").map((item) => item.trim()).filter(Boolean));
    return;
  }
  if (props.definition.type === "integer") {
    emitValue(Number.parseInt(value, 10));
    return;
  }
  if (props.definition.type === "number") {
    emitValue(Number.parseFloat(value));
    return;
  }
  emitValue(value);
}
</script>
