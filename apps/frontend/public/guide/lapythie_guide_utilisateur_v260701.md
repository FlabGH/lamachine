# LaPythie - guide utilisateur

Version integree au front de pilotage : 2026-07-01.

## Setup local

- API : `http://127.0.0.1:8000`
- Front de pilotage : `http://127.0.0.1:5173/ui/` en dev Vite, `/ui/` via Caddy.
- Qdrant : `http://127.0.0.1:6333`
- PostgreSQL Docker LaPythie : `127.0.0.1:55432`

`DATABASE_URL` et `QDRANT_URL` sont les URLs internes Docker. Les scripts lances depuis l'hote utilisent `LAPYTHIE_LOCAL_DATABASE_URL` et `LAPYTHIE_LOCAL_QDRANT_URL`.

## Pipeline documentaire

Le pipeline couvre :

1. ingestion PDF ou texte brut ;
2. validation des metadata ;
3. extraction par loader ;
4. enrichisseurs optionnels ;
5. chunking ;
6. indexation Qdrant ;
7. recherche hybride ;
8. audit par runs.

## Metadata

Les metadata sont exposees par `GET /api/metadata/schema`.

Attributs principaux :

- `type` : type attendu (`enum`, `free`, `boolean`, `number`, `integer`, `date`, `datetime`, `object`, `list`).
- `project_input` : `required`, `optional` ou `forbidden`.
- `propagate_to_chunks` : propagation document vers chunk.
- `propagate_to_qdrant` : presence dans le payload Qdrant.
- `retrieval_filterable` : champ utilisable comme filtre de recherche.
- `values_owner` et `values` : liste de valeurs autorisees.
- `description` : aide fonctionnelle affichable.

Les champs `project_input: forbidden` ne doivent pas etre fournis par le manifest ou le frontend.

### Presentation des metadata

Le registre peut aussi piloter l'affichage des champs dans le front :

- `presentation_group` : groupe fonctionnel (`project`, `description`, `classification`, `source`, `retrieval`, `rights`, `audit`, `technical`).
- `presentation_order` : ordre d'affichage dans le groupe.
- `presentation_importance` : priorite UX (`primary`, `secondary`, `advanced`).
- `presentation_widget` : widget recommande (`text`, `textarea`, `select`, `multiselect`, `tags`, `checkbox`, `number`, `date`, `datetime`, `json`).
- `visible_in` : contextes d'affichage (`ingestion`, `search`, `document`, `chunk`, `catalog`).

`description` reste le champ d'aide utilisateur. Il n'existe pas de champ `help`.

Dans l'ingestion, le front affiche uniquement les metadata visibles dans `ingestion` et declarables par l'utilisateur. Les metadata communes du lot peuvent etre surchargees par les metadata propres au fichier selectionne.

Pour les listes avec `presentation_widget: tags`, le front propose une saisie adaptee :

- si `values` est defini, les valeurs autorisees sont proposees en selection multiple ;
- si `values` est absent ou `null`, la saisie libre de tags est possible.

## Endpoints principaux

- `GET /api/project/config`
- `GET /api/system/summary`
- `GET /api/metadata/schema`
- `GET /api/chunking/strategies`
- `GET /api/loaders`
- `GET /api/enrichers`
- `GET /api/retrieval/presets`
- `GET /api/search/capabilities`
- `GET /api/documents`
- `GET /api/documents/{document_id}/chunks`
- `POST /api/documents/pdf`
- `POST /api/documents/text`
- `POST /api/index`
- `POST /api/search`
- `GET /api/runs`
- `GET /api/runs/{run_id}`

## Limites actuelles

- Pas de batch ingestion backend : le front orchestre les appels fichier par fichier.
- Formats supportes en ingestion : PDF et texte brut.
- Markdown, HTML, CSV et XLSX sont detectes mais affiches non supportes.
- Pas d'edition du registre metadata depuis le front.
- Pas de WebSocket ou suivi temps reel complexe.
- Les enrichisseurs metier reels restent a implementer.
