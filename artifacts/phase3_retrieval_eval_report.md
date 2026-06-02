# Phase 3 Retrieval Evaluation

Generated at: `2026-06-02T15:14:03.589298+00:00`
Manifest: `corpus/poc_ia/manifest.yaml`
Evaluation queries: `corpus/poc_ia/evaluation_queries.yaml`
Index version id: `c898e62f-ff4d-4165-8632-9e490776aca5`
Vector collection: `phase3_step7_eval_20260602151259`

## Metrics

- Recall@5 source_code: 0.812
- Recall@5 role_documentaire: 0.812
- MRR source_code: 0.812
- MRR role_documentaire: 0.812
- Total chunks: 133
- Chunks sans source_code: 0.000
- Chunks sans role_documentaire: 0.000
- Chunks sans page_start/page_end: 0.188

## Query Results

### q01_cdc_snia_bilan

- Query: Quel bilan peut-on faire de la stratégie nationale française pour l’intelligence artificielle ?
- Intent: `cadrage_factuel`
- Expected source_codes: `cour_des_comptes`
- Expected roles: `cadrage_institutionnel`
- Expected theme_tags: `evaluation_publique, ia, strategie_nationale`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 3 | 0.4678 | 0.9826 | 0.0000 | 0.4678 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 10-10 | 34ce2629-eb33-48f8-a18d-4485437d5636 | de la stratégie : viser la diffusion de l'IA dans l'économie Lancée sans évaluation préalable, la deuxième phase de la SNIA était censée relever le défi de la massification et de l'accompagnement de la diffusion de l'intelligence artificielle dans tous les do… | source=yes; role=yes; theme=yes |
| 2 | 2 | 0.3858 | 0.9895 | 0.6176 | 0.3858 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 8-9 | 34ce2629-eb33-48f8-a18d-4485437d5636 | en œuvre de la première phase de la stratégie nationale pour l'intelligence artificielle a permis d'initier une politique publique de l'IA en France, même si elle n'a été en mesure de couvrir qu'une partie des enjeux identifiés en mars 2018. ![img-0.jpeg](img… | source=yes; role=yes; theme=yes |
| 3 | 4 | 0.2539 | 0.9759 | 0.0000 | 0.2539 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | la Commission européenne et membre du Comité IA, ancien coprésident du Conseil national du numérique Dans le rapport de la commission de l’intelli- gence artificielle (IA) auquel vous avez contri- bué, il est indiqué qu’« une mobilisation collective, massive,… | source=no; role=no; theme=yes |
| 4 | 5 | 0.2480 | 0.9739 | 0.0000 | 0.2480 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 6-6 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | des personnalités en capacité de défendre une vision stratégique et de la décliner opérationnellement (nouvelle agence ou ex- tension de prérogatives d’entités existantes,chief AI officer, élu référent en collectivité…). 3. Renforcer la recherche publique pou… | source=no; role=no; theme=yes |
| 5 | 1 | 0.1432 | 1.0000 | 0.6765 | 0.1432 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 11-11 | 34ce2629-eb33-48f8-a18d-4485437d5636 | porté des fruits. Début 2023, la France ne disposait que d'un seul acteur positionné sur ce type de modèle. En quelques mois, l'industrie française a enregistré des progrès en termes de compétitivité et d'attractivité, avec l'émergence d'une dizaine d'acteurs… | source=yes; role=yes; theme=yes |

### q02_cdc_retards_action_publique

- Query: Quels retards la France accuse-t-elle dans la transformation de l’action publique par l’IA ?
- Intent: `cadrage_factuel`
- Expected source_codes: `cour_des_comptes, sens_service_public`
- Expected roles: `cadrage_institutionnel, doctrine_sectorielle`
- Expected theme_tags: `administration, ia, service_public`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.4458 | 0.9940 | 0.9231 | 0.4458 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 11-11 | 34ce2629-eb33-48f8-a18d-4485437d5636 | porté des fruits. Début 2023, la France ne disposait que d'un seul acteur positionné sur ce type de modèle. En quelques mois, l'industrie française a enregistré des progrès en termes de compétitivité et d'attractivité, avec l'émergence d'une dizaine d'acteurs… | source=yes; role=yes; theme=yes |
| 2 | 5 | 0.3451 | 0.9915 | 0.0000 | 0.3451 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 28-28 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ? », 60 millions de consommateurs, 26 janvier 2023. 3. Xavier Biseul, « Chartres met de l’intelligence artificielle dans son standard téléphonique », Acteurs publics, 11 février 2025. 4. Émile Marzolf, « 5 exemples de mise en pratique de l’IA générative dans… | source=yes; role=yes; theme=yes |
| 3 | 4 | 0.2583 | 0.9958 | 0.0000 | 0.2583 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | la Commission européenne et membre du Comité IA, ancien coprésident du Conseil national du numérique Dans le rapport de la commission de l’intelli- gence artificielle (IA) auquel vous avez contri- bué, il est indiqué qu’« une mobilisation collective, massive,… | source=yes; role=yes; theme=yes |
| 4 | 2 | 0.2451 | 1.0000 | 0.0000 | 0.2451 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 5-5 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | venir au niveau local et national seront des occasions de clarifier les différents projets politiques en matière d’IA. Mais n’attendons pas pour en faire dès à présent un objet de débat et de formation à l’intérieur et à l’extérieur de nos organisations publi… | source=yes; role=yes; theme=yes |
| 5 | 3 | 0.1733 | 0.9974 | 0.0000 | 0.1733 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 36-36 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | la gestion d’une partie des tâches à faible valeur ajoutée humaine : celles qui mobilisent du temps, génèrent de la fatigue organisationnelle et freinent la disponibilité pour la relation de service. L’automatisation du traitement des demandes simples, la mis… | source=yes; role=yes; theme=yes |

### q03_service_public_guichet_humain

- Query: Pourquoi faut-il maintenir un guichet humain dans les services publics utilisant l’IA ?
- Intent: `ligne_doctrinale`
- Expected source_codes: `ps, sens_service_public`
- Expected roles: `doctrine_alliee, doctrine_sectorielle`
- Expected theme_tags: `ia, service_public, usagers`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 2 | 0.5397 | 0.9930 | 0.8571 | 0.5397 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 4-4 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | 2025. [PAGE 4] [SECTION Le service public] Le service public à l’épreuve de l’intelligence artiﬁcielle si elles ont simplifié les démarches d’un grand nombre de Françaises et de Français, ont aussi renforcé des formes d’éloignement de l’État et des difficulté… | source=yes; role=yes; theme=yes |
| 2 | 3 | 0.4393 | 1.0000 | 0.0000 | 0.4393 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 28-28 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ? », 60 millions de consommateurs, 26 janvier 2023. 3. Xavier Biseul, « Chartres met de l’intelligence artificielle dans son standard téléphonique », Acteurs publics, 11 février 2025. 4. Émile Marzolf, « 5 exemples de mise en pratique de l’IA générative dans… | source=yes; role=yes; theme=yes |
| 3 | 4 | 0.4282 | 0.9869 | 0.0000 | 0.4282 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 29-29 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | remises en liberté favorise une déresponsabilisation des juges 6. Ces phénomènes s’expliquent notamment par la capacité persuasive des IA génératives. Recommandations pour une IA au service des citoyens Face à ces constats et enjeux, nous proposons plu- sieur… | source=yes; role=yes; theme=yes |
| 4 | 5 | 0.4220 | 0.9827 | 0.0000 | 0.4220 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 27-27 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | déjà mis en place des inventaires à un niveau national. C’est le cas des Pays-Bas1, dont l’inventaire compte à ce jour près d’un millier d’algorithmes et est régulièrement utilisé par la Commission nationale de l’informatique et des libertés (Cnil) et le Défe… | source=yes; role=yes; theme=yes |
| 5 | 1 | 0.3407 | 0.9875 | 0.9286 | 0.3407 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 29-30 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | vol. 65, n°4, 13 mai 2024, pp. 18-19. Le service public à l’épreuve de l’intelligence artiﬁcielle [PAGE 29] [SECTION L’IA dans la relation à l’usager : vers la déshumanisation automatisée ?] L’IA dans la relation à l’usager : vers la déshumanisation automatis… | source=yes; role=yes; theme=yes |

### q04_ia_travail_sens

- Query: Quels effets l’intelligence artificielle peut-elle avoir sur le sens du travail ?
- Intent: `cadrage_social`
- Expected source_codes: `fondation_jean_jaures, sens_service_public`
- Expected roles: `doctrine_alliee, doctrine_sectorielle`
- Expected theme_tags: `emploi, ia, travail`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 4 | 0.5955 | 0.9960 | 0.0000 | 0.5955 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 16-16 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | des agents en permettant d’expéri - menter la technologie à leur niveau sans avoir toujours besoin d’un système spécifique3 ». Les travaux du LaborIA, programme de recherche sur l’IA et le travail initié fin 2021 par le ministère du Travail et de l’Emploi et… | source=yes; role=yes; theme=yes |
| 2 | 2 | 0.5370 | 0.9719 | 0.7917 | 0.5370 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 17-17 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | en jeu leurs ressources subjec- tives, physiques, intellectuelles et émotionnelles, comment se sentir utile, faire du bon travail et s’épa- nouir ? Dans l’autre sens, l’utilisation spontanée et discrète de nombreux agents de solutions grand pu- blic, à leurs… | source=yes; role=yes; theme=yes |
| 3 | 1 | 0.4311 | 0.9829 | 1.0000 | 0.4311 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | forma- lisée, une forte explicabilité, un pilotage continu, une sécurité certifiée, une conformité rigoureuse au Rè- glement général sur la protection des données (RGPD) et au Référentiel général de sécurité (RGS), ainsi qu’une répartition claire des responsa… | source=yes; role=yes; theme=yes |
| 4 | 3 | 0.4258 | 1.0000 | 0.0000 | 0.4258 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 13-13 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | de manière à accompagner le travail humain, développer les expertises internes, est un enjeu et une opportunité pour l’action publique. Pas de « droit à la paresse » : la technologie évolue, les organisations aussi Si l’exigence était déjà induite par la tech… | source=yes; role=yes; theme=yes |
| 5 | 5 | 0.3794 | 0.9715 | 0.0000 | 0.3794 | fondation_jean_jaures | doctrine_alliee | ia, travail, emploi, redistribution, protection_sociale, cohesion_sociale, innovation, europe, souverainete_numerique | 2-2 | 91df4ca9-af2f-4b5f-8837-771d59d03c8e | Les rendements du capital augmenteraient signiﬁcaƟvement. Ce n’est pas enƟèrement nouveau – cela prolonge la dynamique de la révoluƟon industrielle, lorsque les machines permeƩaient à un individu d’accomplir le travail de vingt. L’IA pourrait étendre ce phéno… | source=yes; role=yes; theme=yes |

### q05_ia_redistribution_capital

- Query: Comment partager les gains de productivité liés à l’IA entre capital et travail ?
- Intent: `ligne_doctrinale`
- Expected source_codes: `fondation_jean_jaures`
- Expected roles: `doctrine_alliee`
- Expected theme_tags: `ia, protection_sociale, redistribution`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.6766 | 1.0000 | 1.0000 | 0.6766 | fondation_jean_jaures | doctrine_alliee | ia, travail, emploi, redistribution, protection_sociale, cohesion_sociale, innovation, europe, souverainete_numerique | 2-2 | 91df4ca9-af2f-4b5f-8837-771d59d03c8e | Les rendements du capital augmenteraient signiﬁcaƟvement. Ce n’est pas enƟèrement nouveau – cela prolonge la dynamique de la révoluƟon industrielle, lorsque les machines permeƩaient à un individu d’accomplir le travail de vingt. L’IA pourrait étendre ce phéno… | source=yes; role=yes; theme=yes |
| 2 | 3 | 0.4841 | 0.9755 | 0.0000 | 0.4841 | fondation_jean_jaures | doctrine_alliee | ia, travail, emploi, redistribution, protection_sociale, cohesion_sociale, innovation, europe, souverainete_numerique | 3-3 | 91df4ca9-af2f-4b5f-8837-771d59d03c8e | comme économiques. Ce que je décris est plus ambigu. [PAGE 3] [SECTION Il existe des précédents. Pendant le New Deal, des programmes comme le Civilian ConservaƟon] Il existe des précédents. Pendant le New Deal, des programmes comme le Civilian ConservaƟon Cor… | source=yes; role=yes; theme=yes |
| 3 | 5 | 0.2798 | 0.9639 | 0.0000 | 0.2798 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 17-18 | d7aebaba-867f-412d-bae2-8dd230f65092 | collecte, de recyclage et de réemploi des terminaux obsolètes. 40 [PAGE 17] [SECTION PROJET SOCIALISTE] PROJET SOCIALISTE # Chapitre 5 Mettre le progrès technique au service du progrès humain # Mettre l'intelligence artificielle au service du bien commun L'in… | source=no; role=yes; theme=yes |
| 4 | 2 | 0.2214 | 0.9764 | 0.0000 | 0.2214 | fondation_jean_jaures | doctrine_alliee | ia, travail, emploi, redistribution, protection_sociale, cohesion_sociale, innovation, europe, souverainete_numerique | 6-6 | 91df4ca9-af2f-4b5f-8837-771d59d03c8e | réinvesƟs. Cela représente des masses de capital importantes. Pourtant, elles ne sont pas forcément orientées vers des invesƟssements d’avenir comme l’IA. Quel rôle ce secteur pourrait-il jouer ? Je trouve ces formes alternaƟves d’entreprise intéressantes – i… | source=yes; role=yes; theme=yes |
| 5 | 4 | 0.1956 | 0.9703 | 0.0000 | 0.1956 | fondation_jean_jaures | doctrine_alliee | ia, travail, emploi, redistribution, protection_sociale, cohesion_sociale, innovation, europe, souverainete_numerique | 5-5 | 91df4ca9-af2f-4b5f-8837-771d59d03c8e | bien plus grand qu’il ne l’était dans les années 1940 et 1950. À l’époque, le capital était moins mobile et la coordinaƟon entre grandes puissances plus forte. Aujourd’hui, la mobilité est élevée, la coordinaƟon faible et la capacité de contrainte sur le capi… | source=yes; role=yes; theme=yes |

### q06_ps_ia_bien_commun

- Query: Que propose le Parti socialiste pour mettre l’intelligence artificielle au service du bien commun ?
- Intent: `doctrine_partisane`
- Expected source_codes: `ps`
- Expected roles: `doctrine_alliee`
- Expected theme_tags: `democratie, ia, regulation, service_public`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.7372 | 1.0000 | 0.9000 | 0.7372 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 17-18 | d7aebaba-867f-412d-bae2-8dd230f65092 | collecte, de recyclage et de réemploi des terminaux obsolètes. 40 [PAGE 17] [SECTION PROJET SOCIALISTE] PROJET SOCIALISTE # Chapitre 5 Mettre le progrès technique au service du progrès humain # Mettre l'intelligence artificielle au service du bien commun L'in… | source=yes; role=yes; theme=yes |
| 2 | 3 | 0.6270 | 0.9705 | 0.7333 | 0.6270 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 15-15 | d7aebaba-867f-412d-bae2-8dd230f65092 | plutôt que vers l'intérêt général. Les effets sont déjà visibles. Notre temps d'attention devient une marchandise, l'école et les familles sont débordées par les écrans, le débat public est manipulé par la désinformation. Reprendre la main sur le progrès tech… | source=yes; role=yes; theme=yes |
| 3 | 2 | 0.5756 | 0.9824 | 0.7333 | 0.5756 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 16-17 | d7aebaba-867f-412d-bae2-8dd230f65092 | et les manipulations politiques. Rendre les algorithmes transparents et réellement contrôlables, à travers une obligation de transparence algorithmique pour toute grande plateforme, et la possibilité pour chaque utilisateur d'accéder à un fil non-personnalisé… | source=yes; role=yes; theme=yes |
| 4 | 5 | 0.4858 | 0.9700 | 0.0000 | 0.4858 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 19-19 | d7aebaba-867f-412d-bae2-8dd230f65092 | et en eau. dits refroidissement par immersion, à l'huile. &gt; Lutter contre les manipulations du débat public par l'IA en imposant un marquage clair et obligatoire de tous les contenus multimédia (images, sons, vidéos) générés par IA et en renforçant le juge… | source=yes; role=yes; theme=yes |
| 5 | 4 | 0.4424 | 0.9706 | 0.0000 | 0.4424 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 46-46 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | et l’utilisation des données privées, nous serons des clients à perpétuité de technologies conçues ailleurs. Enfin, à l’instar des citoyennes et citoyens, l’État et les collectivités expérimentent l’IA à grande vitesse, parfois sous prétexte d’une promesse d’… | source=no; role=no; theme=yes |

### q07_ps_plateformes_algorithmes

- Query: Quelles mesures proposer contre les plateformes numériques et leurs algorithmes ?
- Intent: `doctrine_partisane`
- Expected source_codes: `ps`
- Expected roles: `doctrine_alliee`
- Expected theme_tags: `plateformes, regulation, souverainete_numerique`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.5931 | 1.0000 | 1.0000 | 0.5931 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 16-17 | d7aebaba-867f-412d-bae2-8dd230f65092 | et les manipulations politiques. Rendre les algorithmes transparents et réellement contrôlables, à travers une obligation de transparence algorithmique pour toute grande plateforme, et la possibilité pour chaque utilisateur d'accéder à un fil non-personnalisé… | source=yes; role=yes; theme=yes |
| 2 | 2 | 0.5655 | 0.9789 | 0.7692 | 0.5655 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 15-15 | d7aebaba-867f-412d-bae2-8dd230f65092 | plutôt que vers l'intérêt général. Les effets sont déjà visibles. Notre temps d'attention devient une marchandise, l'école et les familles sont débordées par les écrans, le débat public est manipulé par la désinformation. Reprendre la main sur le progrès tech… | source=yes; role=yes; theme=yes |
| 3 | 3 | 0.1968 | 0.9779 | 0.6154 | 0.1968 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 26-26 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | deux cadres réglementaires ne sont pas sans limites, et beaucoup de systèmes algorithmiques cri- tiques vont rester invisibles. En France, les algo - rithmes couverts par certains secrets sont exemptés de ces obligations, dont les algorithmes de lutte contre… | source=no; role=no; theme=no |
| 4 | 5 | 0.1582 | 0.9637 | 0.0000 | 0.1582 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 24-24 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | février 2025. 3. Le Baromètre de l’Observatoire Data Publica 2024 : les collectivités territoriales et la donnée, Observatoire Data Publica, 2024. 4. Sébastien Gavois, « Comment fonctionnent les algorithmes de Parcoursup », Next, 8 mars 2025. 5. Gabriel Geige… | source=no; role=no; theme=no |
| 5 | 4 | 0.1530 | 0.9614 | 0.5769 | 0.1530 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 25-25 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | », IA Ciudadana, 13 mars 2025. 8. Algorithmes, systèmes d’IA et services publics : quels droits pour les usagers ? Points de vigilance et recommandations, Défenseur des droits, 13 novembre 2024. Le service public à l’épreuve de l’intelligence artiﬁcielle [PAG… | source=no; role=no; theme=no |

### q08_lfi_souverainete_numerique

- Query: Quelle est la position de LFI sur la souveraineté numérique et l’accès à Internet ?
- Intent: `comparaison_alliee`
- Expected source_codes: `lfi`
- Expected roles: `doctrine_alliee`
- Expected theme_tags: `bien_commun, services_publics, souverainete_numerique`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.2337 | 1.0000 | 1.0000 | 0.2337 | lfi | doctrine_alliee | ia, souverainete_numerique, logiciels_libres, services_publics, regulation, innovation, infrastructures, bien_commun | 8-8 | 767901a1-3875-45d7-8eee-e73770b48d46 | et privés dans l'espace, luxe ultra polluant réservé à une minorité - Garantir l'utilisation de Galileo par le grand public en rendant obligatoire la double compatibilité Galileo GPS ## Affirmer le caractère d'intérêt général de la révolution numérique La rév… | source=yes; role=yes; theme=yes |
| 2 | 2 | 0.1451 | 0.9794 | 0.5789 | 0.1451 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 15-15 | d7aebaba-867f-412d-bae2-8dd230f65092 | plutôt que vers l'intérêt général. Les effets sont déjà visibles. Notre temps d'attention devient une marchandise, l'école et les familles sont débordées par les écrans, le débat public est manipulé par la désinformation. Reprendre la main sur le progrès tech… | source=no; role=yes; theme=yes |
| 3 | 4 | 0.1312 | 0.9810 | 0.4737 | 0.1312 | lfi | doctrine_alliee | ia, souverainete_numerique, logiciels_libres, services_publics, regulation, innovation, infrastructures, bien_commun |  | 767901a1-3875-45d7-8eee-e73770b48d46 | agence publique des logiciels libres chargée de planifier leur développement stratégique domaine par domaine en identifiant les manques et en finançant les projets-clés - Généraliser l'usage des logiciels libres dans les administrations publiques et l'Éducati… | source=yes; role=yes; theme=yes |
| 4 | 5 | 0.1128 | 0.9711 | 0.4737 | 0.1128 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 16-17 | d7aebaba-867f-412d-bae2-8dd230f65092 | et les manipulations politiques. Rendre les algorithmes transparents et réellement contrôlables, à travers une obligation de transparence algorithmique pour toute grande plateforme, et la possibilité pour chaque utilisateur d'accéder à un fil non-personnalisé… | source=no; role=yes; theme=yes |
| 5 | 3 | 0.0901 | 0.9751 | 0.5263 | 0.0901 | lfi | doctrine_alliee | ia, souverainete_numerique, logiciels_libres, services_publics, regulation, innovation, infrastructures, bien_commun | 7-7 | 767901a1-3875-45d7-8eee-e73770b48d46 | énergétique et d'une maîtrise publique des installations et réseaux tout en veillant à concilier les usages en mer - Mettre en œuvre un plan d'urgence pour l'éolien maritime d'un point de vue énergétique et industriel, garantir le développement de la filière… | source=yes; role=yes; theme=yes |

### q09_lfi_ia_reseaux_sociaux_big_data

- Query: Que propose LFI pour encadrer l’IA, les réseaux sociaux et le big data ?
- Intent: `comparaison_alliee`
- Expected source_codes: `lfi`
- Expected roles: `doctrine_alliee`
- Expected theme_tags: `ia, regulation, reseaux_sociaux`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 2 | 0.2436 | 0.9969 | 0.6429 | 0.2436 | lfi | doctrine_alliee | ia, souverainete_numerique, logiciels_libres, services_publics, regulation, innovation, infrastructures, bien_commun |  | 767901a1-3875-45d7-8eee-e73770b48d46 | agence publique des logiciels libres chargée de planifier leur développement stratégique domaine par domaine en identifiant les manques et en finançant les projets-clés - Généraliser l'usage des logiciels libres dans les administrations publiques et l'Éducati… | source=yes; role=yes; theme=yes |
| 2 | 4 | 0.2200 | 0.9941 | 0.0000 | 0.2200 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 7-9 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | en énergie plutôt que les grands modèles généralistes coûteux et énergivores. Consommant moins d’énergie car ils nécessitent moins de puis - sance de calcul et des serveurs moins performants, ces modèles peuvent être très efficaces pour des tâches ciblées (cl… | source=no; role=no; theme=yes |
| 3 | 1 | 0.2006 | 0.9978 | 0.7143 | 0.2006 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 15-15 | d7aebaba-867f-412d-bae2-8dd230f65092 | plutôt que vers l'intérêt général. Les effets sont déjà visibles. Notre temps d'attention devient une marchandise, l'école et les familles sont débordées par les écrans, le débat public est manipulé par la désinformation. Reprendre la main sur le progrès tech… | source=no; role=yes; theme=yes |
| 4 | 5 | 0.1836 | 0.9931 | 0.0000 | 0.1836 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 17-18 | d7aebaba-867f-412d-bae2-8dd230f65092 | collecte, de recyclage et de réemploi des terminaux obsolètes. 40 [PAGE 17] [SECTION PROJET SOCIALISTE] PROJET SOCIALISTE # Chapitre 5 Mettre le progrès technique au service du progrès humain # Mettre l'intelligence artificielle au service du bien commun L'in… | source=no; role=yes; theme=yes |
| 5 | 3 | 0.1144 | 1.0000 | 0.0000 | 0.1144 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 16-17 | d7aebaba-867f-412d-bae2-8dd230f65092 | et les manipulations politiques. Rendre les algorithmes transparents et réellement contrôlables, à travers une obligation de transparence algorithmique pour toute grande plateforme, et la possibilité pour chaque utilisateur d'accéder à un fil non-personnalisé… | source=no; role=yes; theme=yes |

### q10_rn_ia_energie_reindustrialisation

- Query: Que dit le RN sur le lien entre intelligence artificielle, énergie et réindustrialisation ?
- Intent: `riposte_adversaire`
- Expected source_codes: `rn`
- Expected roles: `opposition`
- Expected theme_tags: `energie, ia, industrie`
- Hit source_code @5: no
- Hit role_documentaire @5: no

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 2 | 0.2568 | 1.0000 | 0.0000 | 0.2568 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 17-18 | d7aebaba-867f-412d-bae2-8dd230f65092 | collecte, de recyclage et de réemploi des terminaux obsolètes. 40 [PAGE 17] [SECTION PROJET SOCIALISTE] PROJET SOCIALISTE # Chapitre 5 Mettre le progrès technique au service du progrès humain # Mettre l'intelligence artificielle au service du bien commun L'in… | source=no; role=no; theme=yes |
| 2 | 4 | 0.1192 | 0.9876 | 0.0000 | 0.1192 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 18-19 | 34ce2629-eb33-48f8-a18d-4485437d5636 | dimension européenne et internationale (Premier ministre, ministère de l'économie, des finances et de la souveraineté industrielle et énergétique, ministère chargé de l'enseignement supérieur et de la recherche, ministère de l'Europe et des affaires étrangère… | source=no; role=no; theme=yes |
| 3 | 3 | 0.1067 | 0.9885 | 0.0000 | 0.1067 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 16-17 | 34ce2629-eb33-48f8-a18d-4485437d5636 | souci de garantir la souveraineté nationale. 15 [PAGE 16] . [PAGE 17] [SECTION # Recommandations] # Recommandations 1. Renforcer, d'ici fin 2025, le pilotage interministériel de la politique publique de l'IA par la constitution d'un secrétariat général ad hoc… | source=no; role=no; theme=yes |
| 4 | 5 | 0.0827 | 0.9808 | 0.0000 | 0.0827 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 8-9 | 34ce2629-eb33-48f8-a18d-4485437d5636 | en œuvre de la première phase de la stratégie nationale pour l'intelligence artificielle a permis d'initier une politique publique de l'IA en France, même si elle n'a été en mesure de couvrir qu'une partie des enjeux identifiés en mars 2018. ![img-0.jpeg](img… | source=no; role=no; theme=yes |
| 5 | 1 | 0.0601 | 0.9927 | 0.6818 | 0.0601 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 11-11 | 34ce2629-eb33-48f8-a18d-4485437d5636 | porté des fruits. Début 2023, la France ne disposait que d'un seul acteur positionné sur ce type de modèle. En quelques mois, l'industrie française a enregistré des progrès en termes de compétitivité et d'attractivité, avec l'émergence d'une dizaine d'acteurs… | source=no; role=no; theme=yes |

### q11_rn_souverainete_numerique

- Query: Existe-t-il une doctrine RN claire sur la souveraineté numérique et l’intelligence artificielle ?
- Intent: `riposte_adversaire`
- Expected source_codes: `rn`
- Expected roles: `opposition`
- Expected theme_tags: `ia, souverainete_numerique`
- Hit source_code @5: no
- Hit role_documentaire @5: no

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.3234 | 1.0000 | 0.0000 | 0.3234 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ciblés et maîtrisés de recours à l’IA pour des métiers précis et des priorités politiques assumées, en refusant expli- citement les dérives et les offres fantaisistes qui pul- lulent, et en informant les citoyens de ces usages tout en concertant leurs dévelop… | source=no; role=no; theme=yes |
| 2 | 4 | 0.2767 | 0.9776 | 0.0000 | 0.2767 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | la Commission européenne et membre du Comité IA, ancien coprésident du Conseil national du numérique Dans le rapport de la commission de l’intelli- gence artificielle (IA) auquel vous avez contri- bué, il est indiqué qu’« une mobilisation collective, massive,… | source=no; role=no; theme=yes |
| 3 | 2 | 0.2465 | 0.9840 | 0.0000 | 0.2465 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 47-47 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | française en IA (INRIA, CNRS, universités) est historiquement de haut niveau. Mais elle est aujourd’hui sous-financée face à la puissance des investissements privés. Le laboratoire commun entre l’INRIA et l’AP-HP développe, par exemple, des algorithmes d’aide… | source=no; role=no; theme=yes |
| 4 | 5 | 0.1790 | 0.9759 | 0.0000 | 0.1790 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 39-39 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | de financement, éva- lué par la commission sur l’IA à 5 milliards d’euros par an d’investissement public pendant cinq ans 5, notamment dans la technologie, mais nous avons aussi un besoin d’expertise internalisée au sein des administrations. Le rapport de la… | source=no; role=no; theme=yes |
| 5 | 3 | 0.1634 | 0.9788 | 0.0000 | 0.1634 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 6-6 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | des personnalités en capacité de défendre une vision stratégique et de la décliner opérationnellement (nouvelle agence ou ex- tension de prérogatives d’entités existantes,chief AI officer, élu référent en collectivité…). 3. Renforcer la recherche publique pou… | source=no; role=no; theme=yes |

### q12_extreme_droite_images_ia

- Query: Comment l’extrême droite utilise-t-elle les images générées par IA en campagne électorale ?
- Intent: `riposte_adversaire`
- Expected source_codes: `lemonde`
- Expected roles: `presse_analyse`
- Expected theme_tags: `campagne_electorale, contenus_generatifs, extreme_droite, ia`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.8366 | 1.0000 | 1.0000 | 0.8366 | lemonde | presse_analyse | ia, politique, campagne_electorale, democratie, desinformation, reseaux_sociaux, extreme_droite, contenus_generatifs | 5-12 | b5d04ad1-4dc0-469a-ac4e-efcb37105967 | 11:05 [PAGE 5] [SECTION LA SUITE APRÈS CETTE PUBLICITÉ] LA SUITE APRÈS CETTE PUBLICITÉ Comment l’extrême droite a utilisé l’intelligence artificielle pour faire la campagne des législatives https://www.lemonde.fr/pixels/article/2024/07/04/legislatives-2024-co… | source=yes; role=yes; theme=yes |
| 2 | 3 | 0.7982 | 0.9935 | 0.5147 | 0.7982 | lemonde | presse_analyse | ia, politique, campagne_electorale, democratie, desinformation, reseaux_sociaux, extreme_droite, contenus_generatifs | 11-13 | b5d04ad1-4dc0-469a-ac4e-efcb37105967 | l’intelligence artificielle pour faire la campagne des législatives https://www.lemonde.fr/pixels/article/2024/07/04/legislatives-2024-comment-l-extreme-droite... 10 sur 13 13/05/2026, 11:05 [PAGE 11] [SECTION sympathisants d’extrême droite. MONTAGE « LE MOND… | source=yes; role=yes; theme=yes |
| 3 | 2 | 0.6715 | 0.9722 | 0.7794 | 0.6715 | lemonde | presse_analyse | ia, politique, campagne_electorale, democratie, desinformation, reseaux_sociaux, extreme_droite, contenus_generatifs | 1-7 | b5d04ad1-4dc0-469a-ac4e-efcb37105967 | [PAGE 1] [SECTION MONTAGE « LE MONDE » D’APRÈS LES COMPTES X DE @ZOLTAN_47 ET @ZEMMOURERIC] MONTAGE « LE MONDE » D’APRÈS LES COMPTES X DE @ZOLTAN_47 ET @ZEMMOURERIC I N T E L L I G E N C E S A R T I F I C I E L L E S G É N É R AT I V E S Proche-Orient Hantavi… | source=yes; role=yes; theme=yes |
| 4 | 5 | 0.3285 | 0.9202 | 0.0000 | 0.3285 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 17-18 | d7aebaba-867f-412d-bae2-8dd230f65092 | collecte, de recyclage et de réemploi des terminaux obsolètes. 40 [PAGE 17] [SECTION PROJET SOCIALISTE] PROJET SOCIALISTE # Chapitre 5 Mettre le progrès technique au service du progrès humain # Mettre l'intelligence artificielle au service du bien commun L'in… | source=no; role=no; theme=yes |
| 5 | 4 | 0.1722 | 0.9231 | 0.0000 | 0.1722 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | tion d’informer les usagers en cas d’utilisation d’un algorithme pour les décisions qui les concernent. Cette obligation trouve sa source dans l’article 15 de la Déclaration des droits de l’homme et du citoyen selon lequel « la société a le droit de demander… | source=no; role=no; theme=yes |

### q13_desinformation_ia_elections

- Query: Quels risques l’IA générative fait-elle peser sur les campagnes électorales et le débat démocratique ?
- Intent: `cadrage_factuel`
- Expected source_codes: `lemonde, ps`
- Expected roles: `doctrine_alliee, presse_analyse`
- Expected theme_tags: `democratie, desinformation, ia`
- Hit source_code @5: no
- Hit role_documentaire @5: no

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.2983 | 0.9982 | 0.7500 | 0.2983 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 11-11 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | risques inhérents à ces derniers, et transversale pour l’IA générative (IAG). ll a notamment interdit certaines pratiques, par exemple la notation sociale, et définit des règles proportionnelles aux risques par nature des usages – en matière de santé, de sécu… | source=no; role=no; theme=yes |
| 2 | 5 | 0.2870 | 0.9963 | 0.0000 | 0.2870 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 10-10 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | terme générique d’IA, se cache une tech- nologie reposant sur une combinaison de ressources – données, algorithmes et infrastructures de calcul –, dont la qualité, l’accès et le contrôle conditionnent à la fois ses performances et ses effets. De la donnée Les… | source=no; role=no; theme=yes |
| 3 | 3 | 0.2583 | 0.9998 | 0.0000 | 0.2583 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | tion d’informer les usagers en cas d’utilisation d’un algorithme pour les décisions qui les concernent. Cette obligation trouve sa source dans l’article 15 de la Déclaration des droits de l’homme et du citoyen selon lequel « la société a le droit de demander… | source=no; role=no; theme=yes |
| 4 | 2 | 0.1801 | 1.0000 | 0.0000 | 0.1801 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 28-28 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | que « cette réponse a été facili- tée par l’IA à 88 %, après traitement et validation par un agent ». Cet exemple de validation dit de « l’humain dans la boucle » est censé compenser les déficiences des IA. Si tel était le cas, les nom - breuses catastrophes… | source=no; role=no; theme=yes |
| 5 | 4 | 0.1176 | 0.9978 | 0.0000 | 0.1176 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 42-42 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | novembre 2024. Enquête menée auprès d’un échantillon de 289 collectivités et établissements publics locaux représentatif de la diversité des collectivités françaises. 5. « Montpellier interdit temporairement ChatGPT à ses agents et engage un travail éthique »… | source=no; role=no; theme=yes |

### q14_ethique_dignite_humaine

- Query: Pourquoi l’intelligence artificielle ne peut-elle pas être considérée comme moralement neutre ?
- Intent: `cadrage_normatif`
- Expected source_codes: `magnifica_humanitas`
- Expected roles: `doctrine_ethique`
- Expected theme_tags: `anthropologie, ethique, ia`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.7800 | 1.0000 | 0.0000 | 0.7800 | magnifica_humanitas | doctrine_ethique | ia, ethique, anthropologie, bien_commun, technique, gouvernance, justice_sociale, transhumanisme | 4-4 | eecbe2b0-20f0-4b8f-bf41-62b6dd90dc89 | durables aﬁn de réduire l’impact sur l’environnement et de prendre soin de notre Maison commune. [124] Responsabilité, transparence et gouvernance de l’IA [PAGE 4] 102. L’uƟlisaƟon de l’IA n’est jamais un fait purement technique : lorsqu’elle intervient dans… | source=yes; role=yes; theme=yes |
| 2 | 2 | 0.4364 | 0.9868 | 0.0000 | 0.4364 | magnifica_humanitas | doctrine_ethique | ia, ethique, anthropologie, bien_commun, technique, gouvernance, justice_sociale, transhumanisme | 3-3 | eecbe2b0-20f0-4b8f-bf41-62b6dd90dc89 | d’un double engagement : d’une part, un approfondissement de la recherche scienƟﬁque ; d’autre part, un exercice de discernement moral et spirituel. 99. Il n’est pas possible de donner une déﬁniƟon univoque et complète de l’IA. Ce que nous pouvons aﬃrmer, c’e… | source=yes; role=yes; theme=yes |
| 3 | 4 | 0.3739 | 0.9847 | 0.0000 | 0.3739 | magnifica_humanitas | doctrine_ethique | ia, ethique, anthropologie, bien_commun, technique, gouvernance, justice_sociale, transhumanisme | 5-5 | eecbe2b0-20f0-4b8f-bf41-62b6dd90dc89 | uƟliser” ; il introduit déjà un critère qui contredit la dignité inaliénable de la personne. C’est pourquoi le discernement éthique ne peut se limiter à se demander si nous uƟlisons un certain système à des ﬁns bonnes ou mauvaises, mais doit également s’inter… | source=yes; role=yes; theme=yes |
| 4 | 5 | 0.3442 | 0.9806 | 0.0000 | 0.3442 | magnifica_humanitas | doctrine_ethique | ia, ethique, anthropologie, bien_commun, technique, gouvernance, justice_sociale, transhumanisme |  | eecbe2b0-20f0-4b8f-bf41-62b6dd90dc89 | condiƟons d’accès, les règles de visibilité et les possibilités de parƟcipaƟon. Lorsqu’un pouvoir d’une telle ampleur se concentre entre quelques mains, il tend à devenir opaque et à échapper au contrôle public, et augmente le risque d’un développement faussé… | source=yes; role=yes; theme=yes |
| 5 | 3 | 0.1413 | 0.9854 | 0.0000 | 0.1413 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 17-17 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | Le service public à l’épreuve de l’intelligence artiﬁcielle 1. « Intelligence artificielle et action publique : construire la confiance, servir la performance », Conseil d’État, op. cit., 2022, p. 94. [PAGE 17] [SECTION 16] 16 IA et éducation : faire avec ou… | source=no; role=no; theme=yes |

### q15_technocratie_bien_commun

- Query: Comment critiquer le paradigme technocratique dans le déploiement de l’IA ?
- Intent: `cadrage_normatif`
- Expected source_codes: `magnifica_humanitas, sens_service_public`
- Expected roles: `doctrine_ethique, doctrine_sectorielle`
- Expected theme_tags: `bien_commun, gouvernance, technique`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 4 | 0.2689 | 0.9953 | 0.0000 | 0.2689 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | connaissances, de personnalisation des actions, d’économies budgétaires, d’amélioration de la performance des politiques. De nombreuses offres commerciales à l’attention du service public vantent bien plus la performance possible du système que la performance… | source=yes; role=yes; theme=no |
| 2 | 2 | 0.2674 | 0.9959 | 0.0000 | 0.2674 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | été fondatrice pour la réactualisation que j’ai tenté d’en faire dans mon essai T echnopouvoir2. La thèse centrale en est simple : toutes les technolo- gies sont toujours en même temps des technologies de pouvoir ; toutes les manières de gouverner et de contr… | source=yes; role=yes; theme=no |
| 3 | 3 | 0.2056 | 0.9955 | 0.0000 | 0.2056 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 28-28 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | que « cette réponse a été facili- tée par l’IA à 88 %, après traitement et validation par un agent ». Cet exemple de validation dit de « l’humain dans la boucle » est censé compenser les déficiences des IA. Si tel était le cas, les nom - breuses catastrophes… | source=yes; role=yes; theme=no |
| 4 | 1 | 0.1836 | 1.0000 | 0.0000 | 0.1836 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | Commençons par intégrer dans tous les appels d’of- fres publics une clause de transparence et d’explica- bilité algorithmique et un cadre clair sur la maîtrise des données d’entrée et de sortie. Généralisons l’usage raisonné de l’IA comme formation obligatoir… | source=yes; role=yes; theme=no |
| 5 | 5 | 0.1613 | 0.9942 | 0.0000 | 0.1613 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ce point de vue, la France a plutôt fait preuve de volontarisme. Mais il me semble hasardeux de mettre tous nos œufs dans le panier de ce projet, tant il dépend peu de nous en tant que citoyens et de la France en tant que puissance souveraine. Je propose dans… | source=yes; role=yes; theme=no |

### q16_synthese_progressiste

- Query: Quels principes progressistes défendre pour une IA démocratique, sociale et souveraine ?
- Intent: `synthese_doctrinale`
- Expected source_codes: `cour_des_comptes, fondation_jean_jaures, ps, sens_service_public`
- Expected roles: `cadrage_institutionnel, doctrine_alliee, doctrine_sectorielle`
- Expected theme_tags: `democratie, ia, service_public, souverainete_numerique`
- Hit source_code @5: yes
- Hit role_documentaire @5: yes

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 2 | 0.5051 | 1.0000 | 0.0000 | 0.5051 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ciblés et maîtrisés de recours à l’IA pour des métiers précis et des priorités politiques assumées, en refusant expli- citement les dérives et les offres fantaisistes qui pul- lulent, et en informant les citoyens de ces usages tout en concertant leurs dévelop… | source=yes; role=yes; theme=yes |
| 2 | 1 | 0.4918 | 0.9979 | 1.0000 | 0.4918 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 17-18 | d7aebaba-867f-412d-bae2-8dd230f65092 | collecte, de recyclage et de réemploi des terminaux obsolètes. 40 [PAGE 17] [SECTION PROJET SOCIALISTE] PROJET SOCIALISTE # Chapitre 5 Mettre le progrès technique au service du progrès humain # Mettre l'intelligence artificielle au service du bien commun L'in… | source=yes; role=yes; theme=yes |
| 3 | 5 | 0.3540 | 0.9844 | 0.0000 | 0.3540 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 6-6 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | des personnalités en capacité de défendre une vision stratégique et de la décliner opérationnellement (nouvelle agence ou ex- tension de prérogatives d’entités existantes,chief AI officer, élu référent en collectivité…). 3. Renforcer la recherche publique pou… | source=yes; role=yes; theme=yes |
| 4 | 3 | 0.2894 | 0.9896 | 0.0000 | 0.2894 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 47-47 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | française en IA (INRIA, CNRS, universités) est historiquement de haut niveau. Mais elle est aujourd’hui sous-financée face à la puissance des investissements privés. Le laboratoire commun entre l’INRIA et l’AP-HP développe, par exemple, des algorithmes d’aide… | source=yes; role=yes; theme=yes |
| 5 | 4 | 0.0995 | 0.9852 | 0.0000 | 0.0995 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 16-17 | d7aebaba-867f-412d-bae2-8dd230f65092 | et les manipulations politiques. Rendre les algorithmes transparents et réellement contrôlables, à travers une obligation de transparence algorithmique pour toute grande plateforme, et la possibilité pour chaque utilisateur d'accéder à un fil non-personnalisé… | source=yes; role=yes; theme=yes |
