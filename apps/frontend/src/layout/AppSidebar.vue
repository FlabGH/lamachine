<template>
  <aside class="sidebar">
    <div class="sidebar__brand">
      <div class="sidebar__brand-title">LaPythie</div>
      <div class="sidebar__brand-subtitle">Pilotage documentaire</div>
    </div>
    <nav class="sidebar__nav">
      <button
        v-for="item in items"
        :key="item.id"
        class="sidebar__item"
        :class="{ 'is-active': item.id === activeView }"
        type="button"
        @click="$emit('navigate', item.id)"
      >
        {{ item.label }}
      </button>
    </nav>
  </aside>
</template>

<script setup>
defineProps({
  items: { type: Array, required: true },
  activeView: { type: String, required: true },
});

defineEmits(["navigate"]);
</script>
