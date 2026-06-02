# Phase 3 PS Weak Layout OCR Diagnostic

Index version: `c898e62f-ff4d-4165-8632-9e490776aca5`

Query: `q06_ps_ia_bien_commun`

`Que propose le Parti socialiste pour mettre l’intelligence artificielle au service du bien commun ?`

## Extraction Metadata After

- method: `pypdf.extract_text+mistral.layout_ocr`
- status: `success`
- ocr_used: `true`
- ocr_provider: `mistral`
- ocr_model: `mistral-ocr-latest`
- ocr_trigger_reason: `weak_layout_quality`
- ocr_pages_processed: `10`
- layout_quality_rules_version: `weak-layout-v1`
- layout_quality_status: `improved_by_ocr`
- layout_suspect_pages: `[1, 4, 7, 11, 14, 15, 16, 17, 18, 19]`
- layout_ocr_pages_requested: `[1, 4, 7, 11, 14, 15, 16, 17, 18, 19]`
- layout_ocr_pages_replaced: `[4, 7, 11, 14, 15, 16, 17, 18, 19]`
- layout_ocr_pages_kept_original: `[1]`
- layout_warnings: `["short_text_page"]`

## Page 17 Before

- chars: `507`
- words: `71`

```text
41
et des terres rares, et entre en concurrence
À l’école, son usage massif sans encadrement
renforce les inégalités d’accès au savoir.
souveraine et transparente, en créant
d’industrialisation pour développer des
sensibles, et accélérer l’industrialisation
souverains dans les services publics, avec
Reprendre la maîtrise démocratique de
l’IA enconditionnant le déploiement des
audits réguliers de conformité aux valeurs
d’interdiction de générer de la nudité, de
l’État au capital des acteurs nationaux de
```

## Page 17 After

- source: `ocr`
- chars: `2337`
- words: `334`
- layout_quality: `improved_by_ocr`

```text
PROJET SOCIALISTE

# Chapitre 5 Mettre le progrès technique au service du progrès humain

# Mettre l'intelligence artificielle au service du bien commun

L'intelligence artificielle ouvre des possibilités immenses pour le progrès humain : automatiser les tâches répétitives, libérer du temps de travail, améliorer les services publics ou la prévention en santé. Mais, livrée aux seules logiques de marché, sans maîtrise démocratique, elle pourrait devenir un facteur de dérives sociales, écologiques et démocratiques. L'IA est énergivore, dépendante des énergies fossiles et des terres rares, et entre en concurrence avec les besoins que fait naître la bifurcation écologique. Elle concentre aujourd'hui ses bénéfices entre les mains de quelques grandes entreprises et actionnaires, tandis que les travailleurs manquent de formation et de protections face aux destructions d'emplois. À l'école, son usage massif sans encadrement renforce les inégalités d'accès au savoir. Elle fragilise aussi nos démocraties par la manipulation de l'information et la dépendance à des plateformes privées étrangères, opaques et non souveraines. La révolution de l'IA ne doit pas enrichir une oligarchie, mais être planifiée démocratiquement pour servir le bien commun.

> Bâtir une Intelligence Artificielle éthique, souveraine et transparente, en créant un pôle public de l'intelligence artificielle associant le CNRS, les universités et des entreprises, et à travers un plan national d'industrialisation pour développer des capacités de calcul et de cloud souverains. Sécuriser le stockage, des données sensibles, et accélérer l'industrialisation de puces stratégiques pour l'IA sur le sol national. Prioriser les outils open source et souverains dans les services publics, avec une sortie progressive des IA génératives fermées, pour éviter toute dépendance à des solutions opaques ou étrangères.

> Reprendre la maîtrise démocratique de l'IA en conditionnant le déploiement des modèles d'IA génératives en Europe à des audits réguliers de conformité aux valeurs européennes de non-discrimination, d'interdiction de générer de la nudité, de transparence et de sécurité. Faire entrer l'État au capital des acteurs nationaux de l'IA, afin de maintenir un contrôle public et favoriser des usages à haute valeur ajoutée sociale et environnementale.
```

## Page 18 Before

- chars: `806`
- words: `134`

```text
42
Investir dans des systèmes de
refroidissement des Data centers plus
économes en énergie et en eau, dits
Lutter contre les manipulations du débat
public par l’IA en imposant un marquage
clair et obligatoire de tous les contenus
multimédia (images, sons, vidéos) générés
par IA et en renforçant le juge électoral
d’un pôle d’experts du numérique et de
l’IA, pour assurer le bon déroulement des
campagnes.
Anticiper l’impact de l’IA sur l’ emploi et
les organisations du travail, pour conjurer
partage de la valeur et du temps de travail,
Faire de l’ école un pilier de l’ égalité face
à l’IA en formant les enseignants et les
Utiliser l’IA pour améliorer la qualité du
service public
des dossiers pour réduire les délais,
orienter les usagers dans leurs démarches)
sans jamais supprimer le guichet humain.
```

## Page 18 After

- source: `ocr`
- chars: `1380`
- words: `218`
- layout_quality: `improved_by_ocr`

```text
PROJET SOCIALISTE

> Investir dans des systèmes de refroidissement des Data centers plus économes en énergie et en eau. dits refroidissement par immersion, à l'huile.
> Lutter contre les manipulations du débat public par l'IA en imposant un marquage clair et obligatoire de tous les contenus multimédia (images, sons, vidéos) générés par IA et en renforçant le juge électoral d'un pôle d'experts du numérique et de l'IA, pour assurer le bon déroulement des campagnes.
> Anticiper l'impact de l'IA sur l'emploi et les organisations du travail, pour conjurer la déqualification des travailleurs et redistribuer les gains de productivité : un gain de rentabilité de 29 % est attendu, en parallèle de disparition d'emplois massives. L'IA doit nous permettre de réquestionner le partage de la valeur et du temps de travail, financée par la création d'une redevance sur l'IA. Une grande loi sur l'IA dans le travail doit être étudiée, étendue à la question de la robotisation.
> Faire de l'école un pilier de l'égalité face à l'IA en formant les enseignants et les élèves, dès le collège, aux usages critiques de l'IA générative pour éviter une fracture éducative.
> Utiliser l'IA pour améliorer la qualité du service public (pré-analyse automatique des dossiers pour réduire les délais, orienter les usagers dans leurs démarches) sans jamais supprimer le guichet humain.
```

## Page 19 Before

- chars: `802`
- words: `109`

```text
43
nous aurions besoin d’investir dans la sobriété
réorienterons vers des innovations utiles.
Renforcer la recherche publique française
et européenne. En France, porter
les fonds du programme « ,
de développer des infrastructures de
Renforcer le pilotage démocratique de
l’innovation, en conditionnant les aides
publiques à des critères d’utilité sociale
et écologique, et en renforçant le contrôle
parlementaire
Créer un fonds national dédié aux
innovations sociales et démocratiques
les technologies frugales, la recherche
dédiée aux besoins historiquement sous-
recherchés dont ceux des femmes. Lancer
Généraliser la transdisciplinarité, en
particulier l’intégration des sciences
sociales dans les grands programmes
de recherche, pour évaluer et orienter les
innovations selon leurs impacts humains,
```

## Page 19 After

- source: `ocr`
- chars: `2612`
- words: `373`
- layout_quality: `improved_by_ocr`

```text
PROJET SOCIALISTE

# Chapitre 5 Mettre le progrès technique au service du progrès humain

# Miser sur les innovations sociales, écologiques et démocratiques

Le progrès technologique échappe de plus en plus au contrôle démocratique pour se soumettre aux logiques du marché. L'essentiel de la recherche est aujourd'hui financé et orienté par le secteur privé, aux États-Unis comme en Europe, tandis que l'investissement public recule, atteignant en France son plus bas niveau depuis quarante ans. Cette évolution favorise une recherche marchande, au détriment de la recherche fondamentale et des innovations d'intérêt général. Des milliards sont ainsi consacrés à des technologies parfois inutiles, voire dangereuses, alors que les ressources de la planète sont limitées, et que nous aurions besoin d'investir dans la sobriété énergétique. Il est temps de rompre avec l'ère du gadget et d'assumer des choix politiques clairs. Démarchandiser l'innovation est une urgence pour la mettre au service du bien commun plutôt que de la rentabilité à court terme. Nous augmenterons l'effort de recherche et le réorienterons vers des innovations utiles.

> Renforcer la recherche publique française et européenne. En France, porter l'investissement en R&D à hauteur de 3 % du PIB d'ici 2030, ce qui représente un effort de près de 6 Mds€ par an. En Europe, doubler les fonds du programme « Horizon Europe », pour atteindre 200 milliards d'euros, afin de développer des infrastructures de recherche publiques européennes dans les domaines clés (deeptech, quantique, IA, low-tech).

> Renforcer le pilotage démocratique de l'innovation, en conditionnant les aides publiques à des critères d'utilité sociale et écologique, et en renforçant le contrôle parlementaire.
```

## PS Chunks After Reindexation

| dense rank q06 | dense score | chunk_index | pages | chunk_id | excerpt |
|---:|---:|---:|---|---|---|
| 1 | 0.906913 | 7 | 17-18 | `35133c2d-e1cf-4f8e-bfae-c9c785b7a474` | collecte, de recyclage et de réemploi des terminaux obsolètes. 40 [PAGE 17] [SECTION PROJET SOCIALISTE] PROJET SOCIALISTE # Chapitre 5 Mettre le progrès technique au service du progrès humain # Mettre l'intelligence artificielle au service |
| 2 | 0.890959 | 6 | 16-17 | `a3aa7aa9-4045-4f4b-a3c9-afb57b2375ad` | et les manipulations politiques. Rendre les algorithmes transparents et réellement contrôlables, à travers une obligation de transparence algorithmique pour toute grande plateforme |
| 4 | 0.880150 | 5 | 15-15 | `0ef7303c-2aa3-4a5c-bbac-f7fdba88f6f0` | plutôt que vers l'intérêt général. Les effets sont déjà visibles. Notre temps d'attention devient une marchandise, l'école et les familles sont débordées par les écrans |
| 5 | 0.879726 | 8 | 19-19 | `7b7e7ec7-4d59-4994-b225-aefb4a887277` | et en eau. dits refroidissement par immersion, à l'huile. > Lutter contre les manipulations du débat public par l'IA en imposant un marquage clair |

## q06 Top5 Final After Reindexation

| rank | source_code | role_documentaire | pages | score | comment |
|---:|---|---|---|---:|---|
| 1 | ps | doctrine_alliee | 17-18 | 0.7372 | expected hit |
| 2 | ps | doctrine_alliee | 15-15 | 0.6270 | expected hit |
| 3 | ps | doctrine_alliee | 16-17 | 0.5756 | expected hit |
| 4 | ps | doctrine_alliee | 19-19 | 0.4858 | expected hit |
| 5 | sens_service_public | doctrine_sectorielle | 46-46 | 0.4424 | contextual |

## Conclusion

The weak-layout OCR patch restores the PS chapter title and substantive content around "Mettre l'intelligence artificielle au service du bien commun". After reindexation, q06 now returns PS chunks in ranks 1 through 4.
