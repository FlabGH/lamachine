# LaPythie

LaPythie est un core documentaire IA generique. Le setup local expose une API FastAPI, Postgres, Qdrant et un front de pilotage leger.

## Lancement Local

Demarrer la stack :

```bash
docker compose -f infra/compose/docker-compose.yml -f infra/compose/docker-compose.local.yml up -d --build
```

La stack Docker utilise `COMPOSE_PROJECT_NAME=lapythie` par defaut. Cette
variable est un identifiant d'infrastructure Docker : elle prefixe les
conteneurs, volumes et reseaux. Elle est distincte de `project_name`, qui est
une information applicative lue par le backend dans `project.yaml`.

URLs utiles :

- API : `http://127.0.0.1:8000`
- Front de pilotage Vite : `http://127.0.0.1:5173/ui/`
- Front via Caddy : `https://localhost/ui/`
- Qdrant : `http://127.0.0.1:6333`
- PostgreSQL Docker LaPythie : `127.0.0.1:55432`

Le port hote `5432` est volontairement evite pour ne pas entrer en conflit avec un PostgreSQL systeme local.

Les ports hotes peuvent etre ajustes dans `.env` :

- `API_HOST_PORT`
- `FRONTEND_HOST_PORT`
- `POSTGRES_HOST_PORT`
- `QDRANT_HOST_PORT`
- `CADDY_HTTP_PORT`
- `CADDY_HTTPS_PORT`

## Projet Consommateur Local

Un projet consommateur doit garder ses valeurs projet hors des fichiers de
configuration generiques versionnes par LaPythie.

Procedure recommandee :

1. Creer un `.env` propre au projet consommateur.
2. Definir un nom de stack Docker dedie, par exemple
   `COMPOSE_PROJECT_NAME=consumer`.
3. Definir des ports hotes dedies si la stack LaPythie tourne aussi en local.
4. Definir `PROJECT_CONFIG_PATH=config/local/project.yaml`.
5. Creer `apps/api/config/local/project.yaml`.
6. Creer `apps/api/config/local/metadata_registry.project.yaml`.

Dans `apps/api/config/local/project.yaml`, conserver le registre core fourni par
LaPythie et pointer le registre projet vers le fichier local :

```yaml
documentary:
  metadata_registry:
    core: config/metadata_registry.core.yaml
    project: config/local/metadata_registry.project.yaml
```

Les exemples `apps/api/config/project.consumer.example.yaml` et
`apps/api/config/metadata_registry.consumer.example.yaml` donnent une base
neutre a copier dans `apps/api/config/local/`.

Pour synchroniser le core LaPythie dans un checkout consommateur, utiliser :

```bash
scripts/sync_core_to_consumer.sh --target /chemin/du/projet-consommateur
```

La commande est un dry-run par defaut. Appliquer la synchronisation seulement
apres verification :

```bash
scripts/sync_core_to_consumer.sh --target /chemin/du/projet-consommateur --apply
```

Le script ne fait ni `fetch`, ni `checkout`. Il doit etre lance depuis la
branche LaPythie deja validee pour le deploiement. Il exclut volontairement
`.env`, `apps/api/config/local/`, `apps/api/config/project.yaml` et
`apps/api/config/metadata_registry.project.yaml`.

## Front De Pilotage

Le front est dans `apps/frontend`.

Il permet de piloter et consulter :

- etat systeme ;
- ingestion PDF et texte brut ;
- metadata declarables ;
- recherche retrieval ;
- runs et retrieval hits ;
- documents, chunks et extractions ;
- catalogues metadata, chunking, loaders, enrichers et presets ;
- objets documentaires structures ;
- guide utilisateur integre ;
- journal debug des appels API.

Le front consomme les endpoints existants sous `/api`. La route `/ui` est reservee a la SPA frontend ; `/api/*` reste strictement reserve au backend.

## Limites Connues Du Front

- Pas de batch ingestion backend : le batch est orchestre cote frontend par appels successifs.
- Formats supportes en ingestion : PDF et texte brut.
- Markdown, HTML, CSV et XLSX sont detectes comme non supportes tant que les loaders correspondants ne sont pas disponibles.
- Pas d'edition du registre metadata.
- Pas de WebSocket/SSE ; le suivi repose sur les statuts HTTP et les runs existants.
