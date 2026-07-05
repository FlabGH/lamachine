<template>
  <div class="app-shell">
    <AppSidebar :items="navItems" :active-view="activeView" @navigate="activeView = $event" />
    <main class="main">
      <AppHeader :title="currentItem.label" :subtitle="currentItem.description">
        <AppBadge>{{ apiBaseLabel }}</AppBadge>
      </AppHeader>
      <section class="content">
        <component :is="currentItem.component" />
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import AppBadge from "./components/ui/AppBadge.vue";
import AppHeader from "./layout/AppHeader.vue";
import AppSidebar from "./layout/AppSidebar.vue";
import { API_BASE_URL } from "./config";
import CatalogsView from "./views/CatalogsView.vue";
import ChunkingPreviewView from "./views/ChunkingPreviewView.vue";
import DashboardView from "./views/DashboardView.vue";
import DocumentsView from "./views/DocumentsView.vue";
import GuideView from "./views/GuideView.vue";
import IndexingView from "./views/IndexingView.vue";
import IngestionView from "./views/IngestionView.vue";
import RunsView from "./views/RunsView.vue";
import SearchView from "./views/SearchView.vue";
import StructuredObjectsView from "./views/StructuredObjectsView.vue";
import ApiDebugView from "./views/ApiDebugView.vue";

const navItems = [
  { id: "dashboard", label: "Accueil", description: "Etat du systeme", component: DashboardView },
  { id: "ingestion", label: "Ingestion", description: "Ajouter des documents", component: IngestionView },
  { id: "search", label: "Recherche", description: "Interroger le corpus", component: SearchView },
  { id: "runs", label: "Runs", description: "Audit et traces", component: RunsView },
  { id: "documents", label: "Documents", description: "Explorer le corpus", component: DocumentsView },
  { id: "chunking", label: "Chunking", description: "Previsualiser le decoupage", component: ChunkingPreviewView },
  { id: "indexing", label: "Indexation", description: "Construire un index", component: IndexingView },
  { id: "objects", label: "Objets", description: "Objets documentaires structures", component: StructuredObjectsView },
  { id: "catalogs", label: "Catalogues", description: "Schemas et capacites", component: CatalogsView },
  { id: "guide", label: "Guide", description: "Documentation integree", component: GuideView },
  { id: "debug", label: "Debug API", description: "Derniers appels frontend", component: ApiDebugView },
];

const activeView = ref("dashboard");
const currentItem = computed(() => navItems.find((item) => item.id === activeView.value) || navItems[0]);
const apiBaseLabel = computed(() => `API ${API_BASE_URL}`);
</script>
