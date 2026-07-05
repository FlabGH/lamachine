# LaPythie

LaPythie est un core documentaire IA generique. Le setup local expose une API FastAPI, Postgres, Qdrant et un front de pilotage leger.

## Lancement Local

Demarrer la stack :

```bash
docker compose -f infra/compose/docker-compose.yml -f infra/compose/docker-compose.local.yml up -d --build
```

URLs utiles :

- API : `http://127.0.0.1:8000`
- Front de pilotage Vite : `http://127.0.0.1:5173/ui/`
- Front via Caddy : `https://localhost/ui/`
- Qdrant : `http://127.0.0.1:6333`
- PostgreSQL Docker LaPythie : `127.0.0.1:55432`

Le port hote `5432` est volontairement evite pour ne pas entrer en conflit avec un PostgreSQL systeme local.

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
