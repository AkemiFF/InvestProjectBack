# Endpoints disponibles

Voici la liste des endpoints disponibles pour l'application "projects":

## Projets

- `GET /api/projects/` - Liste de tous les projets (avec filtrage et pagination)
- `POST /api/projects/` - Créer un nouveau projet
- `GET /api/projects/{id}/` - Détails d'un projet spécifique
- `PUT /api/projects/{id}/` - Mettre à jour un projet (propriétaire uniquement)
- `PATCH /api/projects/{id}/` - Mettre à jour partiellement un projet (propriétaire uniquement)
- `DELETE /api/projects/{id}/` - Supprimer un projet (propriétaire uniquement)
- `POST /api/projects/{id}/add_media/` - Ajouter un média à un projet
- `DELETE /api/projects/{id}/remove_media/` - Supprimer un média d'un projet
- `POST /api/projects/{id}/toggle_favorite/` - Ajouter/Retirer un projet des favoris
- `POST /api/projects/{id}/submit_for_review/` - Soumettre un projet pour validation
- `GET /api/projects/my_projects/` - Liste des projets de l'utilisateur connecté

### Secteurs

- `GET /api/sectors/` - Liste de tous les secteurs d'activité
- `GET /api/sectors/{id}/` - Détails d'un secteur spécifique

## Paramètres de filtrage pour les projets

- `sector` - Filtrer par ID de secteur
- `min_amount` - Montant minimum recherché
- `max_amount` - Montant maximum recherché
- `funding_type` - Type de financement
- `status` - Statut du projet
- `search` - Recherche dans le titre et la description
- `featured=true` - Projets en vedette
- `ending_soon=true` - Projets qui se terminent bientôt
- `new=true` - Nouveaux projets
- `favorites=true` - Projets favoris de l'utilisateur

## Exemples d'utilisation

### Lister tous les projets actifs

```plaintext
GET /api/projects/
```

### Rechercher des projets

```plaintext
GET /api/projects/?search=agriculture&sector=3&min_amount=1000000&max_amount=10000000
```

### Projets en vedette

```plaintext
GET /api/projects/?featured=true
```

### Projets qui se terminent bientôt

```plaintext
GET /api/projects/?ending_soon=true
```

### Créer un nouveau projet

```plaintext
POST /api/projects/
{
    "title": "Projet d'agriculture durable",
    "description": "Description détaillée du projet...",
    "sector_id": 3,
    "funding_type": "equity",
    "amount_needed": 5000000,
    "minimum_investment": 100000,
    "deadline": "2024-06-30",
    "video_url": "https://youtube.com/watch?v=example"
}
```

### Ajouter un média à un projet

POST /api/projects/1/add_media/
Content-Type: multipart/form-data

file: [fichier binaire]
file_type: "image"
title: "Image principale du projet"
