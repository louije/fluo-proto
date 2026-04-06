# Prototype « recos »

Proto créé avec `make new recos`. Voici le contexte et le détail.

# Contexte

C'est encore une app qui reprend l'apparence générale des emplois de l'inclusion, du point de vue d'un prescripteur / orienteur / accompagnateur, typiquement un conseiller France Travail.

L'objectif principal, c'est de *recommander*, pour chaque personne accompagnée, une modalité ou une structure d'accompagnement. Les modalités sont internes à France Travail : aujourd'hui Suivi, Guidé, Renforcé, Global. Bientôt remplacées par Essentiel ou Intensif. Les structures d'accompagnement, au sens de la loi, sont celles qui peuvent se substituer à France Travail ou le compléter en tant qu'accompagnateur principal d'une personne. Ça inclut les SIAE, les PLIE, les E2C, etc.

# Objectif

Le but de ce proto est de faire tester un nouveau parcours d'orientation aux utilisateurs, en partant des fiches individuelles des personnes accompagnées, et en affichant une liste de recommandations de « Solutions de parcours structuré » ou de « Modalités ».

On teste deux choses :
- le parcours utilisateur – est-ce qu'on comprend les recommandations et comment agir dessus
- le moteur de recommandation, qu'on intégrera dans un second temps.

# Structure de l'interface

Le proto doit intégrer ces écrans (et entrées du menu principal) :

- Tableau de bord (Accueil)
- Liste des bénéficiaires (Personnes accompagnées)
- Fiche individuelle (Fiche usager), avec des onglets
- Recommandations d'orientations – c'est le nouvel écran

Le tableau de bord existe déjà dans les emplois. On va le modifier, mais la structure globale (barre de recherche, puis mur de cartes) reste.

La liste existe aussi dans les emplois (et dans les anciens protos comme « demandes »). Les intitulés de colonnes vont changer, mais l'architecture générale reste.

La fiche individuelle existe dans les emplois (et dans les anciens protos). Les onglets vont un peu bouger – on ajoute un onglet Diagnostic socio-professionnel. Le gros bouton bleu d'action en haut à droite sera renommé (Orienter, ou Prescrire, ou scindé entre Prescrire et Candidater, on verra).

Les Recommandations, c'est nouveau. Ça ressemblera à une page de résultats de recherche. On itérera sur le design au fur et à mesure.

# Données

Dans `/Users/louije/Development/gip/explorations-nova/diags`, il y a des fichiers JSON qui correspondent à des diagnostics socio-professionnels très réalistes. Le modèle de données du DSP est dans `/Users/louije/Development/gip/ftio/schemas/diagnostic-usager.json`, mais on n'a pas besoin de s'en occuper pour l'instant. On a 4 diagnostics, on part avec ceux-là.

Par la suite, il faudra créer d'autres situations inspirées de ces quatre-là, ou les déplacer géographiquement. Mais pas maintenant.

# Design détaillé

## Accueil

Le tableau de bord a 2 zones principales.

### Barre de recherche

La barre de recherche est « universelle ». Elle permet de chercher dans toute l'app (lieux, comme aujourd'hui, SIAE, structures, services, personnes). Pour l'instant, on le suggère avec ce texte de placeholder : Rechercher une personne, une structure, un emploi...

On ne développe pas la fonctionnalité de recherche pour l'instant.

### Cartes

Les cartes sont disposées en grille automatique. Les grands écrans en affichent 3 par ligne, la plupart 2, le mobile 1.

Première carte : « Personnes accompagnées ». Elle indique le nombre de personnes dans le « Portefeuille », autour de 70. Puis elle met en avant 3 chiffres :

- « 1 dossier sans solution » (personnes pour qui toutes les demandes d'orientation en cours ont été refusées)
- « 5 réponses à des demandes d'orientation » (qui peuvent être positives – acceptées, négatives – refusées, ou neutres : demande d'infos complémentaires)
- « 1 personne en fin de parcours », sous-titre « Anticiper la sortie de cette personne »

En bas de cette carte, un lien vers la liste des Personnes, intitulé « Voir tous les dossiers ».

Deuxième carte : « En ce moment sur mon territoire », avec par exemple « Prochain comité local : personnes isolées et santé mentale », avec une date et un lieu, ou « Nouveaux services référencés : Mobilité (3), Hébergement (1) », ou encore « 3 nouvelles fiches de poste en SIAE ». Les formulations sont indicatives, on peut itérer.

Troisième carte : « Organisation », similaire à celle qu'on a aujourd'hui côté Prescripteurs.

## Liste des Personnes accompagnées

Liste classique (voir `job-seekers/list`). Colonnes :

- Nom Prénom
- Éligibilité
- Nbr prescriptions
- Modalité / structure référente

L'éligibilité contient des badges arrondis (rounded-pill). Ceux-ci peuvent être (comme sur les pages « Candidats » actuelles des emplois) :

- PASS IAE valide
- Éligibilité IAE à valider

Mais aussi :

- Éligible PLIE
- Éligible EPIDE
- Éligible E2C

Quand la personne n'est pas éligible, on n'affiche rien. Quand c'est peut-être éligible, on ajoute « à valider ». On verra plus tard comment calculer ça.

Nbr prescriptions additionne les trois types de prescriptions : les « Candidatures IAE » d'origine, les « Orientations vers des services d'insertion » en cours de dev, et les futures « Orientations vers une solution de parcours ou une modalité ».

Modalité / structure référente correspond à ce troisième type. Ça peut être :

- Inconnue
- Un nom de modalité France Travail
- Le nom d'une structure avec son acronyme, comme « Jardins de Cocagne (ACI) », ou « Lille Avenir (PLIE) », ou « Ville de Montluçon (CCAS) ».

## Fiche personne

Similaire à l'actuelle `job-seekers/details`. Onglets :

- Informations générales
- Diagnostic (nouveau, voir les fichiers JSON et le dossier diags dans explorations-nova)
- Prescriptions (remplace Candidatures)

Informations générales affiche la modalité ou la structure référente en premier bloc, au-dessus des Informations générales (c'est l'un ou l'autre, selon). Un bouton (outline primary) invite à la modifier, et mène vers l'écran de recommandations d'orientations.

Le CTA principal de la page Personne n'est plus « Postuler pour ce candidat » mais « Prescrire une solution ». Ce qui, pour l'instant, mène aussi vers l'écran de recommandations.

## Écran de recommandations d'orientations

Comme sur l'actuel `search/employers/results?job_seeker_public_id=9f495d51...`, il y a une barre de statut (`alert alert-primary fade show`) qui dit « Vous postulez actuellement pour... ».

Sauf que le titre n'est plus « Rechercher un emploi inclusif » mais « Rechercher une solution », et les onglets sont « Employeurs (SIAE et GEIQ) », « Postes ouverts », « Services d'insertion », « Solutions de parcours », ce dernier étant sélectionné par défaut quand on arrive depuis le bouton de la barre Modalités.

# Plan de développement

Deux temps pour l'instant.

1. Menu et structure. Créer l'architecture générale à la les-emplois, avec les pages principales (Accueil, Personnes accompagnées), en ajoutant au menu principal « Demandes envoyées » et « Demandes reçues ». Les pages principales (tableau de bord, liste, fiche individuelle) s'appuieront largement sur les emplois actuels.

2. Données. Itérer sur les 4 fichiers JSON pour déterminer ce qui manque ou ce qu'il faut ajouter pour qu'ils s'intègrent dans les templates.

3. Pause pour relecture.
4. Intégrer le moteur de recommandation.
