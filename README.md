# BURGEAPLY

**Plateforme d'ingénierie environnementale avancée**

Une application desktop moderne pour les professionnels de l'environnement, offrant des outils de cartographie, d'analyse de données et de traitement de rapports laboratoire.

---

## 🚀 Fonctionnalités

### GéoToolbox
- Extraction de données géographiques (BSS, BDLisa, etc.)
- Visualisation cartographique interactive
- Export de données en formats standards

### Chronologie Complète (OrthoHisto)
- Génération automatique de chronologies de photographies aériennes
- Historique complet d'un site géoréférencé

### AutoLabo
- Traitement automatique des rapports de laboratoire (AGROLAB, EUROFINS à venir)
- Support des matrices Eaux Souterraines et Sols
- Génération de tableaux Excel formatés avec seuils réglementaires
- Formatage conditionnel intelligent

### Feedback & Support
- Système de retour utilisateur intégré
- Notifications de mises à jour automatiques

---

## 📦 Installation

### Prérequis
- Python 3.10+
- Windows 10/11

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Lancement
```bash
python app.py
```

---

## 🏗️ Architecture

```
├── app.py                 # Point d'entrée principal
├── modules/
│   ├── autolabo.py        # Module de traitement laboratoire
│   ├── autolabo_core/     # Configuration YAML multi-laboratoires
│   ├── geotoolbox.py      # Module GéoToolbox
│   ├── geotoolbox_core/   # Parsers et exporters GéoToolbox
│   ├── orthohisto.py      # Module Chronologie
│   ├── feedback.py        # Module Feedback
│   ├── about.py           # Module À Propos
│   ├── core.py            # Utilitaires partagés
│   ├── updater.py         # Système de mise à jour
│   └── version.py         # Gestion des versions
├── assets/
│   ├── templates/         # Templates HTML Jinja2
│   ├── css/               # Styles CSS
│   ├── js/                # JavaScript frontend
│   └── img/               # Images et icônes
├── ressources/            # Fichiers de référence (seuils réglementaires)
├── config.json            # Configuration utilisateur
├── requirements.txt       # Dépendances Python
└── Burgeaply.spec         # Configuration PyInstaller
```

---

## 🔧 Configuration

Le fichier `config.json` contient la configuration de l'application :

```json
{
  "app": {
    "debug": false,
    "version": "2.0.0"
  }
}
```

---

## 📋 Technologies

- **Backend**: Python 3.10+, Pandas, XlsxWriter
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **UI Framework**: PyWebView
- **Configuration**: Pydantic, PyYAML
- **Packaging**: PyInstaller

---

## 👨‍💻 Développement

### Structure des modules AutoLabo

L'architecture AutoLabo utilise un système de configuration YAML :

```
modules/autolabo_core/
├── config/
│   ├── models.py          # Modèles Pydantic
│   ├── registry.py        # Chargement des configurations
│   └── providers/
│       └── agrolab/
│           ├── provider.yaml
│           ├── eaux.yaml
│           └── sols.yaml
└── processors/
    └── base.py            # GenericLabProcessor
```

---

## 📝 Licence

Propriétaire - GINGER BURGEAP

---

## 👤 Auteur

**Laurent BRIGAUD**  
Développé pour GINGER BURGEAP
