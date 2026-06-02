# Phase 3 Retrieval Evaluation

Generated at: `2026-06-02T09:35:07.095567+00:00`
Manifest: `corpus/poc_ia/manifest.yaml`
Evaluation queries: `corpus/poc_ia/evaluation_queries.yaml`
Index version id: `4f9e4abd-0108-4370-a250-1ed15ff95e9b`
Vector collection: `phase3_step7_eval_20260602092512`

## Metrics

- Recall@5 source_code: 0.750
- Recall@5 role_documentaire: 0.750
- MRR source_code: 0.719
- MRR role_documentaire: 0.719
- Total chunks: 126
- Chunks sans source_code: 0.000
- Chunks sans role_documentaire: 0.000
- Chunks sans page_start/page_end: 0.183

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
| 2 | 5 | 0.4369 | 0.9738 | 0.0000 | 0.4369 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 46-46 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ailleurs. Enfin, à l’instar des citoyennes et citoyens, l’État et les collectivités expérimentent l’IA à grande vitesse, parfois sous prétexte d’une promesse d’efficacité ou d’économies budgétaires. Mais sans cadre public clair, ces usages peuvent vite dérive… | source=no; role=no; theme=yes |
| 3 | 2 | 0.3858 | 0.9895 | 0.6000 | 0.3858 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 8-9 | 34ce2629-eb33-48f8-a18d-4485437d5636 | en œuvre de la première phase de la stratégie nationale pour l'intelligence artificielle a permis d'initier une politique publique de l'IA en France, même si elle n'a été en mesure de couvrir qu'une partie des enjeux identifiés en mars 2018. ![img-0.jpeg](img… | source=yes; role=yes; theme=yes |
| 4 | 4 | 0.2282 | 0.9761 | 0.0000 | 0.2282 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | numérique Dans le rapport de la commission de l’intelli- gence artificielle (IA) auquel vous avez contri- bué, il est indiqué qu’« une mobilisation collective, massive, sans délai et au long cours est impérative ». Où en sommes-nous aujour- d’hui ? Un certain… | source=no; role=no; theme=yes |
| 5 | 1 | 0.1432 | 1.0000 | 0.6571 | 0.1432 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 11-11 | 34ce2629-eb33-48f8-a18d-4485437d5636 | porté des fruits. Début 2023, la France ne disposait que d'un seul acteur positionné sur ce type de modèle. En quelques mois, l'industrie française a enregistré des progrès en termes de compétitivité et d'attractivité, avec l'émergence d'une dizaine d'acteurs… | source=yes; role=yes; theme=yes |

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
| 1 | 1 | 0.4458 | 0.9896 | 0.9231 | 0.4458 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 11-11 | 34ce2629-eb33-48f8-a18d-4485437d5636 | porté des fruits. Début 2023, la France ne disposait que d'un seul acteur positionné sur ce type de modèle. En quelques mois, l'industrie française a enregistré des progrès en termes de compétitivité et d'attractivité, avec l'émergence d'une dizaine d'acteurs… | source=yes; role=yes; theme=yes |
| 2 | 2 | 0.2806 | 1.0000 | 0.0000 | 0.2806 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 5-5 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques en matière d’IA. Mais n’attendons pas pour en faire dès à présent un objet de débat et de formation à l’intérieur et à l’extérieur de nos organisations publiques. 1. « Un tiers des adultes ont renoncé à effectuer une démarche administrative », Inse… | source=yes; role=yes; theme=yes |
| 3 | 4 | 0.2598 | 0.9915 | 0.0000 | 0.2598 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | numérique Dans le rapport de la commission de l’intelli- gence artificielle (IA) auquel vous avez contri- bué, il est indiqué qu’« une mobilisation collective, massive, sans délai et au long cours est impérative ». Où en sommes-nous aujour- d’hui ? Un certain… | source=yes; role=yes; theme=yes |
| 4 | 3 | 0.2018 | 0.9931 | 0.0000 | 0.2018 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 36-36 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | mobilisent du temps, génèrent de la fatigue organisationnelle et freinent la disponibilité pour la relation de service. L’automatisation du traitement des demandes simples, la mise à jour des plannings hospitaliers ou la reconfiguration des tâches quotidienne… | source=yes; role=yes; theme=yes |
| 5 | 5 | 0.1160 | 0.9867 | 0.0000 | 0.1160 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 6-6 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | (nouvelle agence ou ex- tension de prérogatives d’entités existantes,chief AI officer, élu référent en collectivité…). 3. Renforcer la recherche publique pour une IA d’intérêt général Cibler une part significative du budget sur la recherche en IA d’intérêt gé… | source=yes; role=yes; theme=yes |

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
| 1 | 2 | 0.5301 | 1.0000 | 0.0000 | 0.5301 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 28-28 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | met de l’intelligence artificielle dans son standard téléphonique », Acteurs publics, 11 février 2025. 4. Émile Marzolf, « 5 exemples de mise en pratique de l’IA générative dans le secteur public », Acteurs publics, 2 juillet 2024. À l’heure des choix budgéta… | source=yes; role=yes; theme=yes |
| 2 | 4 | 0.5162 | 0.9938 | 0.0000 | 0.5162 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 5-5 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | artiﬁcielle si elles ont simplifié les démarches d’un grand nombre de Françaises et de Français, ont aussi renforcé des formes d’éloignement de l’État et des difficultés d’accès aux dispositifs1. À ce stade, l’IA pourrait tout aussi bien résoudre ces probléma… | source=yes; role=yes; theme=yes |
| 3 | 3 | 0.4225 | 0.9975 | 0.0000 | 0.4225 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 29-29 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | la capacité persuasive des IA génératives. Recommandations pour une IA au service des citoyens Face à ces constats et enjeux, nous proposons plu- sieurs mesures. Du côté des usagers, il est indispensable de garantir le droit à une interaction directe avec un… | source=yes; role=yes; theme=yes |
| 4 | 5 | 0.3567 | 0.9907 | 0.0000 | 0.3567 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 5-5 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques en matière d’IA. Mais n’attendons pas pour en faire dès à présent un objet de débat et de formation à l’intérieur et à l’extérieur de nos organisations publiques. 1. « Un tiers des adultes ont renoncé à effectuer une démarche administrative », Inse… | source=yes; role=yes; theme=yes |
| 5 | 1 | 0.2365 | 0.9911 | 0.8276 | 0.2365 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 29-30 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | l’intelligence artiﬁcielle [PAGE 29] [SECTION L’IA dans la relation à l’usager : vers la déshumanisation automatisée ?] L’IA dans la relation à l’usager : vers la déshumanisation automatisée ? à la fois des acteurs internes aux administrations (ins- pecteurs,… | source=yes; role=yes; theme=yes |

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
| 1 | 4 | 0.5936 | 0.9920 | 0.0000 | 0.5936 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 16-16 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | toujours besoin d’un système spécifique3 ». Les travaux du LaborIA, programme de recherche sur l’IA et le travail initié fin 2021 par le ministère du Travail et de l’Emploi et l’Institut national de recherche en sciences et technologies du numérique (Inria),… | source=yes; role=yes; theme=yes |
| 2 | 3 | 0.4732 | 1.0000 | 0.0000 | 0.4732 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 13-13 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | et une opportunité pour l’action publique. Pas de « droit à la paresse » : la technologie évolue, les organisations aussi Si l’exigence était déjà induite par la technologie et son encadrement, le RIA introduit de façon encore plus explicite l’obligation de s… | source=yes; role=yes; theme=yes |
| 3 | 1 | 0.4140 | 0.9825 | 1.0000 | 0.4140 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | au Rè- glement général sur la protection des données (RGPD) et au Référentiel général de sécurité (RGS), ainsi qu’une répartition claire des responsabilités. Si l’alignement des SIA sur les exigences d’un service public performant au service de l’intérêt géné… | source=yes; role=yes; theme=yes |
| 4 | 2 | 0.3794 | 0.9694 | 0.7500 | 0.3794 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 15-15 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | choix technologiques doi - vent préserver la souveraineté nationale, notamment par la maîtrise des dépendances critiques, des données sensibles et par le développement de capa- cités européennes). Ces principes garantiraient l’ali- gnement entre les usages de… | source=yes; role=yes; theme=yes |
| 5 | 5 | 0.3789 | 0.9698 | 0.0000 | 0.3789 | fondation_jean_jaures | doctrine_alliee | ia, travail, emploi, redistribution, protection_sociale, cohesion_sociale, innovation, europe, souverainete_numerique | 2-2 | 91df4ca9-af2f-4b5f-8837-771d59d03c8e | Les rendements du capital augmenteraient signiﬁcaƟvement. Ce n’est pas enƟèrement nouveau – cela prolonge la dynamique de la révoluƟon industrielle, lorsque les machines permeƩaient à un individu d’accomplir le travail de vingt. L’IA pourrait étendre ce phéno… | source=yes; role=yes; theme=yes |

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
| 3 | 2 | 0.2214 | 0.9764 | 0.0000 | 0.2214 | fondation_jean_jaures | doctrine_alliee | ia, travail, emploi, redistribution, protection_sociale, cohesion_sociale, innovation, europe, souverainete_numerique | 6-6 | 91df4ca9-af2f-4b5f-8837-771d59d03c8e | réinvesƟs. Cela représente des masses de capital importantes. Pourtant, elles ne sont pas forcément orientées vers des invesƟssements d’avenir comme l’IA. Quel rôle ce secteur pourrait-il jouer ? Je trouve ces formes alternaƟves d’entreprise intéressantes – i… | source=yes; role=yes; theme=yes |
| 4 | 4 | 0.1956 | 0.9703 | 0.0000 | 0.1956 | fondation_jean_jaures | doctrine_alliee | ia, travail, emploi, redistribution, protection_sociale, cohesion_sociale, innovation, europe, souverainete_numerique | 5-5 | 91df4ca9-af2f-4b5f-8837-771d59d03c8e | bien plus grand qu’il ne l’était dans les années 1940 et 1950. À l’époque, le capital était moins mobile et la coordinaƟon entre grandes puissances plus forte. Aujourd’hui, la mobilité est élevée, la coordinaƟon faible et la capacité de contrainte sur le capi… | source=yes; role=yes; theme=yes |
| 5 | 5 | 0.1366 | 0.9686 | 0.0000 | 0.1366 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 13-13 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | et une opportunité pour l’action publique. Pas de « droit à la paresse » : la technologie évolue, les organisations aussi Si l’exigence était déjà induite par la technologie et son encadrement, le RIA introduit de façon encore plus explicite l’obligation de s… | source=no; role=no; theme=yes |

### q06_ps_ia_bien_commun

- Query: Que propose le Parti socialiste pour mettre l’intelligence artificielle au service du bien commun ?
- Intent: `doctrine_partisane`
- Expected source_codes: `ps`
- Expected roles: `doctrine_alliee`
- Expected theme_tags: `democratie, ia, regulation, service_public`
- Hit source_code @5: no
- Hit role_documentaire @5: no

| rank | initial | score | dense | lexical | rerank | source_code | role_documentaire | theme_tags | pages | document_id | extrait | commentaire |
|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | 1 | 0.4550 | 1.0000 | 0.6552 | 0.4550 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 46-46 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ailleurs. Enfin, à l’instar des citoyennes et citoyens, l’État et les collectivités expérimentent l’IA à grande vitesse, parfois sous prétexte d’une promesse d’efficacité ou d’économies budgétaires. Mais sans cadre public clair, ces usages peuvent vite dérive… | source=no; role=no; theme=yes |
| 2 | 2 | 0.2282 | 0.9998 | 0.0000 | 0.2282 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 6-6 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | (nouvelle agence ou ex- tension de prérogatives d’entités existantes,chief AI officer, élu référent en collectivité…). 3. Renforcer la recherche publique pour une IA d’intérêt général Cibler une part significative du budget sur la recherche en IA d’intérêt gé… | source=no; role=no; theme=yes |
| 3 | 4 | 0.2082 | 0.9887 | 0.0000 | 0.2082 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 47-47 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | aujourd’hui sous-financée face à la puissance des investissements privés. Le laboratoire commun entre l’INRIA et l’AP-HP développe, par exemple, des algorithmes d’aide au diagnostic éthique et validés médicalement. C’est un exemple qu’il faudrait suivre. Nous… | source=no; role=no; theme=yes |
| 4 | 5 | 0.2082 | 0.9873 | 0.0000 | 0.2082 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques assumées, en refusant expli- citement les dérives et les offres fantaisistes qui pul- lulent, et en informant les citoyens de ces usages tout en concertant leurs développements. Car au final, ce sont les élues et élus qui décident, et les citoyenne… | source=no; role=no; theme=yes |
| 5 | 3 | 0.1824 | 0.9925 | 0.0000 | 0.1824 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 5-5 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques en matière d’IA. Mais n’attendons pas pour en faire dès à présent un objet de débat et de formation à l’intérieur et à l’extérieur de nos organisations publiques. 1. « Un tiers des adultes ont renoncé à effectuer une démarche administrative », Inse… | source=no; role=no; theme=yes |

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
| 1 | 4 | 0.5433 | 0.9800 | 0.0000 | 0.5433 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 17-19 | d7aebaba-867f-412d-bae2-8dd230f65092 | et l’ARCOM contrôle des algorithmes, doté de moyens prévention et de retrait rapide des contenus haineux par les plateformes, prévues Protéger l’ espace numérique contre les ingérences étrangères, l’usurpation d’identité en ligne ou le vol de données, et de n… | source=yes; role=yes; theme=yes |
| 2 | 2 | 0.2379 | 0.9812 | 0.8333 | 0.2379 | lfi | doctrine_alliee | ia, souverainete_numerique, logiciels_libres, services_publics, regulation, innovation, infrastructures, bien_commun | 8-8 | 767901a1-3875-45d7-8eee-e73770b48d46 | et privés dans l'espace, luxe ultra polluant réservé à une minorité - Garantir l'utilisation de Galileo par le grand public en rendant obligatoire la double compatibilité Galileo GPS ## Affirmer le caractère d'intérêt général de la révolution numérique La rév… | source=no; role=yes; theme=yes |
| 3 | 1 | 0.2134 | 1.0000 | 0.8333 | 0.2134 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 26-26 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | tiques vont rester invisibles. En France, les algo - rithmes couverts par certains secrets sont exemptés de ces obligations, dont les algorithmes de lutte contre la fraude. La Caisse nationale d’allocations familiales a par exemple invoqué cette exception pou… | source=no; role=no; theme=no |
| 4 | 3 | 0.1530 | 0.9876 | 0.0000 | 0.1530 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 24-24 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | et la donnée, Observatoire Data Publica, 2024. 4. Sébastien Gavois, « Comment fonctionnent les algorithmes de Parcoursup », Next, 8 mars 2025. 5. Gabriel Geiger, Soizic Pénicaud, Manon Romain et Adrien Sénécat, « Profilage et discriminations : enquête sur les… | source=no; role=no; theme=no |
| 5 | 5 | 0.1009 | 0.9796 | 0.0000 | 0.1009 | lfi | doctrine_alliee | ia, souverainete_numerique, logiciels_libres, services_publics, regulation, innovation, infrastructures, bien_commun |  | 767901a1-3875-45d7-8eee-e73770b48d46 | agence publique des logiciels libres chargée de planifier leur développement stratégique domaine par domaine en identifiant les manques et en finançant les projets-clés - Généraliser l'usage des logiciels libres dans les administrations publiques et l'Éducati… | source=no; role=yes; theme=yes |

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
| 2 | 3 | 0.1312 | 0.9810 | 0.4737 | 0.1312 | lfi | doctrine_alliee | ia, souverainete_numerique, logiciels_libres, services_publics, regulation, innovation, infrastructures, bien_commun |  | 767901a1-3875-45d7-8eee-e73770b48d46 | agence publique des logiciels libres chargée de planifier leur développement stratégique domaine par domaine en identifiant les manques et en finançant les projets-clés - Généraliser l'usage des logiciels libres dans les administrations publiques et l'Éducati… | source=yes; role=yes; theme=yes |
| 3 | 5 | 0.1176 | 0.9563 | 0.0000 | 0.1176 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 17-19 | d7aebaba-867f-412d-bae2-8dd230f65092 | et l’ARCOM contrôle des algorithmes, doté de moyens prévention et de retrait rapide des contenus haineux par les plateformes, prévues Protéger l’ espace numérique contre les ingérences étrangères, l’usurpation d’identité en ligne ou le vol de données, et de n… | source=no; role=yes; theme=yes |
| 4 | 4 | 0.1082 | 0.9564 | 0.0000 | 0.1082 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 14-16 | d7aebaba-867f-412d-bae2-8dd230f65092 | commune, de la constitution d’un pôle de coopération non Imposer des objectifs en matière de sécurité d’approvisionnement passant notamment par le maintien de stocks mobilisables sur le sol européen dans les Encadrer la robotisation et accompagner la mutation… | source=no; role=yes; theme=yes |
| 5 | 2 | 0.0901 | 0.9751 | 0.5263 | 0.0901 | lfi | doctrine_alliee | ia, souverainete_numerique, logiciels_libres, services_publics, regulation, innovation, infrastructures, bien_commun | 7-7 | 767901a1-3875-45d7-8eee-e73770b48d46 | énergétique et d'une maîtrise publique des installations et réseaux tout en veillant à concilier les usages en mer - Mettre en œuvre un plan d'urgence pour l'éolien maritime d'un point de vue énergétique et industriel, garantir le développement de la filière… | source=yes; role=yes; theme=yes |

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
| 1 | 4 | 0.2494 | 0.9946 | 0.0000 | 0.2494 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 7-9 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | car ils nécessitent moins de puis - sance de calcul et des serveurs moins performants, ces modèles peuvent être très efficaces pour des tâches ciblées (classer des documents, répondre à des questions simples, automatiser des démarches administratives). 9. Inv… | source=no; role=no; theme=yes |
| 2 | 1 | 0.2436 | 1.0000 | 0.7500 | 0.2436 | lfi | doctrine_alliee | ia, souverainete_numerique, logiciels_libres, services_publics, regulation, innovation, infrastructures, bien_commun |  | 767901a1-3875-45d7-8eee-e73770b48d46 | agence publique des logiciels libres chargée de planifier leur développement stratégique domaine par domaine en identifiant les manques et en finançant les projets-clés - Généraliser l'usage des logiciels libres dans les administrations publiques et l'Éducati… | source=yes; role=yes; theme=yes |
| 3 | 5 | 0.1836 | 0.9901 | 0.0000 | 0.1836 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 46-46 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ailleurs. Enfin, à l’instar des citoyennes et citoyens, l’État et les collectivités expérimentent l’IA à grande vitesse, parfois sous prétexte d’une promesse d’efficacité ou d’économies budgétaires. Mais sans cadre public clair, ces usages peuvent vite dérive… | source=no; role=no; theme=yes |
| 4 | 3 | 0.1592 | 0.9946 | 0.0000 | 0.1592 | ps | doctrine_alliee | ia, service_public, regulation, plateformes, innovation, democratie, souverainete_numerique, emploi, recherche | 17-19 | d7aebaba-867f-412d-bae2-8dd230f65092 | et l’ARCOM contrôle des algorithmes, doté de moyens prévention et de retrait rapide des contenus haineux par les plateformes, prévues Protéger l’ espace numérique contre les ingérences étrangères, l’usurpation d’identité en ligne ou le vol de données, et de n… | source=no; role=yes; theme=yes |
| 5 | 2 | 0.1413 | 0.9980 | 0.0000 | 0.1413 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 6-6 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | (nouvelle agence ou ex- tension de prérogatives d’entités existantes,chief AI officer, élu référent en collectivité…). 3. Renforcer la recherche publique pour une IA d’intérêt général Cibler une part significative du budget sur la recherche en IA d’intérêt gé… | source=no; role=no; theme=yes |

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
| 1 | 5 | 0.1330 | 0.9809 | 0.0000 | 0.1330 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques assumées, en refusant expli- citement les dérives et les offres fantaisistes qui pul- lulent, et en informant les citoyens de ces usages tout en concertant leurs développements. Car au final, ce sont les élues et élus qui décident, et les citoyenne… | source=no; role=no; theme=yes |
| 2 | 3 | 0.1200 | 0.9948 | 0.0000 | 0.1200 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 18-19 | 34ce2629-eb33-48f8-a18d-4485437d5636 | dimension européenne et internationale (Premier ministre, ministère de l'économie, des finances et de la souveraineté industrielle et énergétique, ministère chargé de l'enseignement supérieur et de la recherche, ministère de l'Europe et des affaires étrangère… | source=no; role=no; theme=yes |
| 3 | 2 | 0.1082 | 0.9957 | 0.0000 | 0.1082 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 16-17 | 34ce2629-eb33-48f8-a18d-4485437d5636 | souci de garantir la souveraineté nationale. 15 [PAGE 16] . [PAGE 17] [SECTION # Recommandations] # Recommandations 1. Renforcer, d'ici fin 2025, le pilotage interministériel de la politique publique de l'IA par la constitution d'un secrétariat général ad hoc… | source=no; role=no; theme=yes |
| 4 | 4 | 0.0827 | 0.9881 | 0.0000 | 0.0827 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 8-9 | 34ce2629-eb33-48f8-a18d-4485437d5636 | en œuvre de la première phase de la stratégie nationale pour l'intelligence artificielle a permis d'initier une politique publique de l'IA en France, même si elle n'a été en mesure de couvrir qu'une partie des enjeux identifiés en mars 2018. ![img-0.jpeg](img… | source=no; role=no; theme=yes |
| 5 | 1 | 0.0601 | 1.0000 | 0.6522 | 0.0601 | cour_des_comptes | cadrage_institutionnel | ia, strategie_nationale, gouvernance, innovation, recherche, investissement_public, evaluation_publique | 11-11 | 34ce2629-eb33-48f8-a18d-4485437d5636 | porté des fruits. Début 2023, la France ne disposait que d'un seul acteur positionné sur ce type de modèle. En quelques mois, l'industrie française a enregistré des progrès en termes de compétitivité et d'attractivité, avec l'émergence d'une dizaine d'acteurs… | source=no; role=no; theme=yes |

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
| 1 | 1 | 0.3174 | 1.0000 | 0.0000 | 0.3174 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques assumées, en refusant expli- citement les dérives et les offres fantaisistes qui pul- lulent, et en informant les citoyens de ces usages tout en concertant leurs développements. Car au final, ce sont les élues et élus qui décident, et les citoyenne… | source=no; role=no; theme=yes |
| 2 | 3 | 0.2934 | 0.9794 | 0.0000 | 0.2934 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | numérique Dans le rapport de la commission de l’intelli- gence artificielle (IA) auquel vous avez contri- bué, il est indiqué qu’« une mobilisation collective, massive, sans délai et au long cours est impérative ». Où en sommes-nous aujour- d’hui ? Un certain… | source=no; role=no; theme=yes |
| 3 | 4 | 0.2674 | 0.9774 | 0.0000 | 0.2674 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 47-47 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | aujourd’hui sous-financée face à la puissance des investissements privés. Le laboratoire commun entre l’INRIA et l’AP-HP développe, par exemple, des algorithmes d’aide au diagnostic éthique et validés médicalement. C’est un exemple qu’il faudrait suivre. Nous… | source=no; role=no; theme=yes |
| 4 | 5 | 0.1931 | 0.9710 | 0.0000 | 0.1931 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | concernent. Cette obligation trouve sa source dans l’article 15 de la Déclaration des droits de l’homme et du citoyen selon lequel « la société a le droit de demander compte à tout agent public de son administration ». À l’ère de l’IA, le Conseil constitution… | source=no; role=no; theme=yes |
| 5 | 2 | 0.1836 | 0.9796 | 0.0000 | 0.1836 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 6-6 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | (nouvelle agence ou ex- tension de prérogatives d’entités existantes,chief AI officer, élu référent en collectivité…). 3. Renforcer la recherche publique pour une IA d’intérêt général Cibler une part significative du budget sur la recherche en IA d’intérêt gé… | source=no; role=no; theme=yes |

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
| 1 | 1 | 0.7447 | 0.9994 | 1.0000 | 0.7447 | lemonde | presse_analyse | ia, politique, campagne_electorale, democratie, desinformation, reseaux_sociaux, extreme_droite, contenus_generatifs | 1-10 | b5d04ad1-4dc0-469a-ac4e-efcb37105967 | [PAGE 1] [SECTION MONTAGE « LE MONDE » D’APRÈS LES COMPTES X DE @ZOLTAN_47 ET @ZEMMOURERIC] MONTAGE « LE MONDE » D’APRÈS LES COMPTES X DE @ZOLTAN_47 ET @ZEMMOURERIC I N T E L L I G E N C E S A R T I F I C I E L L E S G É N É R AT I V E S Proche-Orient Hantavi… | source=yes; role=yes; theme=yes |
| 2 | 2 | 0.7341 | 1.0000 | 0.5753 | 0.7341 | lemonde | presse_analyse | ia, politique, campagne_electorale, democratie, desinformation, reseaux_sociaux, extreme_droite, contenus_generatifs | 9-13 | b5d04ad1-4dc0-469a-ac4e-efcb37105967 | campagne des législatives https://www.lemonde.fr/pixels/article/2024/07/04/legislatives-2024-comment-l-extreme-droite... 8 sur 13 13/05/2026, 11:05 [PAGE 9] Matteo Salvini a partagé ces images générées par intelligence artiﬁcielle. Sur leur gauche, elles sont… | source=yes; role=yes; theme=yes |
| 3 | 3 | 0.1613 | 0.9447 | 0.0000 | 0.1613 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | concernent. Cette obligation trouve sa source dans l’article 15 de la Déclaration des droits de l’homme et du citoyen selon lequel « la société a le droit de demander compte à tout agent public de son administration ». À l’ère de l’IA, le Conseil constitution… | source=no; role=no; theme=yes |
| 4 | 5 | 0.1403 | 0.9405 | 0.0000 | 0.1403 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 46-46 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ailleurs. Enfin, à l’instar des citoyennes et citoyens, l’État et les collectivités expérimentent l’IA à grande vitesse, parfois sous prétexte d’une promesse d’efficacité ou d’économies budgétaires. Mais sans cadre public clair, ces usages peuvent vite dérive… | source=no; role=no; theme=yes |
| 5 | 4 | 0.1366 | 0.9444 | 0.0000 | 0.1366 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques assumées, en refusant expli- citement les dérives et les offres fantaisistes qui pul- lulent, et en informant les citoyens de ces usages tout en concertant leurs développements. Car au final, ce sont les élues et élus qui décident, et les citoyenne… | source=no; role=no; theme=yes |

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
| 1 | 3 | 0.2958 | 0.9997 | 0.0000 | 0.2958 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | concernent. Cette obligation trouve sa source dans l’article 15 de la Déclaration des droits de l’homme et du citoyen selon lequel « la société a le droit de demander compte à tout agent public de son administration ». À l’ère de l’IA, le Conseil constitution… | source=no; role=no; theme=yes |
| 2 | 2 | 0.2902 | 1.0000 | 0.0000 | 0.2902 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques assumées, en refusant expli- citement les dérives et les offres fantaisistes qui pul- lulent, et en informant les citoyens de ces usages tout en concertant leurs développements. Car au final, ce sont les élues et élus qui décident, et les citoyenne… | source=no; role=no; theme=yes |
| 3 | 1 | 0.2524 | 0.9975 | 0.4375 | 0.2524 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 10-10 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | – données, algorithmes et infrastructures de calcul –, dont la qualité, l’accès et le contrôle conditionnent à la fois ses performances et ses effets. De la donnée Les données sont le carburant de l’IA dont le volume et la qualité conditionnent la performance… | source=no; role=no; theme=yes |
| 4 | 5 | 0.1895 | 0.9945 | 0.0000 | 0.1895 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 28-28 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | traitement et validation par un agent ». Cet exemple de validation dit de « l’humain dans la boucle » est censé compenser les déficiences des IA. Si tel était le cas, les nom - breuses catastrophes n’auraient jamais eu lieu, comme celle du scandale des algori… | source=no; role=no; theme=yes |
| 5 | 4 | 0.1052 | 0.9953 | 0.0000 | 0.1052 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | me semble hasardeux de mettre tous nos œufs dans le panier de ce projet, tant il dépend peu de nous en tant que citoyens et de la France en tant que puissance souveraine. Je propose dans l’ordre quelques idées qui pourraient participer à une appro- priation d… | source=no; role=no; theme=yes |

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
| 2 | 2 | 0.4373 | 0.9868 | 0.0000 | 0.4373 | magnifica_humanitas | doctrine_ethique | ia, ethique, anthropologie, bien_commun, technique, gouvernance, justice_sociale, transhumanisme | 3-3 | eecbe2b0-20f0-4b8f-bf41-62b6dd90dc89 | d’un double engagement : d’une part, un approfondissement de la recherche scienƟﬁque ; d’autre part, un exercice de discernement moral et spirituel. 99. Il n’est pas possible de donner une déﬁniƟon univoque et complète de l’IA. Ce que nous pouvons aﬃrmer, c’e… | source=yes; role=yes; theme=yes |
| 3 | 3 | 0.3757 | 0.9847 | 0.0000 | 0.3757 | magnifica_humanitas | doctrine_ethique | ia, ethique, anthropologie, bien_commun, technique, gouvernance, justice_sociale, transhumanisme | 5-5 | eecbe2b0-20f0-4b8f-bf41-62b6dd90dc89 | uƟliser” ; il introduit déjà un critère qui contredit la dignité inaliénable de la personne. C’est pourquoi le discernement éthique ne peut se limiter à se demander si nous uƟlisons un certain système à des ﬁns bonnes ou mauvaises, mais doit également s’inter… | source=yes; role=yes; theme=yes |
| 4 | 4 | 0.2822 | 0.9817 | 0.0000 | 0.2822 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques assumées, en refusant expli- citement les dérives et les offres fantaisistes qui pul- lulent, et en informant les citoyens de ces usages tout en concertant leurs développements. Car au final, ce sont les élues et élus qui décident, et les citoyenne… | source=no; role=no; theme=yes |
| 5 | 5 | 0.1394 | 0.9817 | 0.0000 | 0.1394 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 17-17 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | publique : construire la confiance, servir la performance », Conseil d’État, op. cit., 2022, p. 94. [PAGE 17] [SECTION 16] 16 IA et éducation : faire avec ou faire sans ? – Diana Filippova1 Romancière et essayiste, autrice de Technopouvoir. Dépolitiser pour m… | source=no; role=no; theme=yes |

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
| 1 | 4 | 0.2910 | 0.9960 | 0.0000 | 0.2910 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 14-14 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | de manière plus générale une réflexion col- lective qui doit être menée sur ces technologies : la constante accélération des rythmes de déploiement ne doit pas empêcher une discussion politique sur les objectifs que nous poursuivons et leur bien- fondé2 », re… | source=yes; role=yes; theme=no |
| 2 | 3 | 0.2736 | 0.9963 | 0.0000 | 0.2736 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | nombreuses offres commerciales à l’attention du service public vantent bien plus la performance possible du système que la performance du service public : on vend des IA qui marchent, mais qui ne servent à rien. Il est ensuite essentiel de se saisir à bras-le… | source=yes; role=yes; theme=no |
| 3 | 2 | 0.2465 | 0.9963 | 0.0000 | 0.2465 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | echnopouvoir2. La thèse centrale en est simple : toutes les technolo- gies sont toujours en même temps des technologies de pouvoir ; toutes les manières de gouverner et de contrôler s’appuient toujours sur des technologies qui, par définition, ne sont pas neu… | source=yes; role=yes; theme=no |
| 4 | 5 | 0.2187 | 0.9957 | 0.0000 | 0.2187 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 36-36 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | mobilisent du temps, génèrent de la fatigue organisationnelle et freinent la disponibilité pour la relation de service. L’automatisation du traitement des demandes simples, la mise à jour des plannings hospitaliers ou la reconfiguration des tâches quotidienne… | source=yes; role=yes; theme=no |
| 5 | 1 | 0.1836 | 1.0000 | 0.0000 | 0.1836 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite |  | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | et d’explica- bilité algorithmique et un cadre clair sur la maîtrise des données d’entrée et de sortie. Généralisons l’usage raisonné de l’IA comme formation obligatoire pour les agents publics. Certaines collectivités ont pris les devants. Ainsi, Nantes métr… | source=yes; role=yes; theme=no |

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
| 1 | 1 | 0.5173 | 1.0000 | 0.0000 | 0.5173 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 45-45 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | politiques assumées, en refusant expli- citement les dérives et les offres fantaisistes qui pul- lulent, et en informant les citoyens de ces usages tout en concertant leurs développements. Car au final, ce sont les élues et élus qui décident, et les citoyenne… | source=yes; role=yes; theme=yes |
| 2 | 5 | 0.3789 | 0.9761 | 0.0000 | 0.3789 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 46-46 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | ailleurs. Enfin, à l’instar des citoyennes et citoyens, l’État et les collectivités expérimentent l’IA à grande vitesse, parfois sous prétexte d’une promesse d’efficacité ou d’économies budgétaires. Mais sans cadre public clair, ces usages peuvent vite dérive… | source=yes; role=yes; theme=yes |
| 3 | 3 | 0.3540 | 0.9806 | 0.0000 | 0.3540 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 47-47 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | aujourd’hui sous-financée face à la puissance des investissements privés. Le laboratoire commun entre l’INRIA et l’AP-HP développe, par exemple, des algorithmes d’aide au diagnostic éthique et validés médicalement. C’est un exemple qu’il faudrait suivre. Nous… | source=yes; role=yes; theme=yes |
| 4 | 2 | 0.2999 | 0.9819 | 0.0000 | 0.2999 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 6-6 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | (nouvelle agence ou ex- tension de prérogatives d’entités existantes,chief AI officer, élu référent en collectivité…). 3. Renforcer la recherche publique pour une IA d’intérêt général Cibler une part significative du budget sur la recherche en IA d’intérêt gé… | source=yes; role=yes; theme=yes |
| 5 | 4 | 0.2862 | 0.9763 | 0.0000 | 0.2862 | sens_service_public | doctrine_sectorielle | ia, service_public, administration, transformation_numerique, contrôle, etat, usagers, formation, qualite | 37-38 | 62f544ad-676d-42a1-93c3-ab549cdd45b2 | La voie d’un humanisme tech- nologique est étroite, mais féconde. Elle suppose une gouvernance démocratique de l’innovation, une régulation des usages, une responsabilité assumée des commanditaires publics. À plus long terme, le défi est celui d’une IA civiqu… | source=yes; role=yes; theme=yes |
