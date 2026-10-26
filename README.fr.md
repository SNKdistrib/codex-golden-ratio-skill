# Nombre d'or et mises en page pour Codex

[English](README.md) · [Contribuer](CONTRIBUTING.md) · [Licence MIT](LICENSE)

Un skill communautaire pour composer des visuels avec des **relations dorées
mesurables**, des marges confortables et des commandes équilibrées.
Écrire « nombre d'or » dans un prompt ne suffit pas : il faut calculer,
implémenter, rendre, mesurer puis inspecter le résultat.

**Projet en développement. Les contributions sont bienvenues.** Une validation
locale ne prouve ni la conformité de toute l'image ni sa beauté.

## Contenu

- Instructions compatibles avec Codex et sélection automatique selon la demande.
- Calculateur de partage doré, sans dépendance Python supplémentaire.
- Vérificateur des alignements, proportions, espacements et zones vides.
- Helper facultatif de mesure du DOM d'une interface rendue.
- Tests, définition mathématique et limites explicites des contrôles.

Les boutons ne doivent pas être grossis artificiellement pour fabriquer φ.
L'ergonomie, la lisibilité et les demandes explicites restent prioritaires.

## Installation

Télécharger `golden-ratio-visual-design.zip` depuis la
[dernière version](https://github.com/SNKdistrib/codex-golden-ratio-skill/releases/latest).
Extraire le dossier `golden-ratio-visual-design` dans `~/.agents/skills/`, soit
normalement `%USERPROFILE%\.agents\skills\` sous Windows.
Sauvegarder toute version existante avant de la remplacer.

Autre possibilité : cloner le dépôt et copier le dossier
`skills/golden-ratio-visual-design` dans le répertoire de skills utilisateur.
Le paquet ne modifie pas automatiquement les préférences globales.

Invocation explicite :

```text
$golden-ratio-visual-design
Compose ce menu avec des marges confortables, puis vérifie la géométrie rendue.
```

La sélection implicite dépend de la description. Une règle personnelle `AGENTS.md`
peut demander son utilisation pour tous les travaux visuels. Si la découverte
n'est pas actualisée, redémarrer Codex.

## Vérifier

Python 3.11+ suffit. Depuis la racine du dépôt :

```sh
python -m unittest discover -s skills/golden-ratio-visual-design/tests -v
python skills/golden-ratio-visual-design/scripts/verify_layout.py --spec contrat.json --measurements mesures.json --image rendu.png --out rapport.json
```

Consulter le [format des mesures](skills/golden-ratio-visual-design/references/verification.md)
avant de préparer les fichiers. Les instructions techniques du paquet sont en anglais.
Les mesures doivent venir du rendu, pas des valeurs demandées au générateur.

Codes de sortie : `0`, les règles déclarées passent ; `1`, au moins un échec ;
`2`, données non vérifiées ou invalides. Le rapport laisse explicitement
`global_composition_conformity: NOT_ESTABLISHED`.

Il n'y a pas d'OCR automatique, de garantie de beauté, d'authentification des
annotations manuelles ou d'audit complet d'accessibilité. Inspecter aussi l'image.

## Participer

Faire un fork, modifier sa copie, exécuter les tests et ouvrir une pull request.
Les mainteneurs vérifient les propositions avant fusion. Les issues permettent
de signaler un problème ou proposer une amélioration.
Voir le [guide de contribution](CONTRIBUTING.md).

Aucune capture personnelle, image de jeu, donnée de compte ou autre skill n'est
publié. Les inspirations sont créditées dans les
[notes de sources](skills/golden-ratio-visual-design/references/sources.md).
