# Endpoints disponibles

Voici la liste des endpoints disponibles pour l'application "comments":

## Commentaires

- `GET /api/comments/` - Liste de tous les commentaires (avec filtrage et pagination)
- `POST /api/comments/` - Créer un nouveau commentaire
- `GET /api/comments/{id}/` - Détails d'un commentaire spécifique
- `PUT /api/comments/{id}/` - Mettre à jour un commentaire (auteur uniquement)
- `PATCH /api/comments/{id}/` - Mettre à jour partiellement un commentaire (auteur uniquement)
- `DELETE /api/comments/{id}/` - Supprimer un commentaire (auteur uniquement)
- `POST /api/comments/{id}/moderate/` - Modérer un commentaire (propriétaire du projet ou admin)
- `GET /api/comments/my_comments/` - Liste des commentaires de l'utilisateur connecté
- `GET /api/comments/pending_moderation/` - Liste des commentaires en attente de modération pour les projets de l'utilisateur

## Paramètres de filtrage pour les commentaires

- `project` - Filtrer par ID de projet
- `root_only=true` - Récupérer uniquement les commentaires de premier niveau (sans parent)
- `author` - Filtrer par ID d'auteur
- `is_approved` - Filtrer par statut d'approbation (true/false)

## Exemples d'utilisation

### Lister tous les commentaires d'un projet

```plaintext
GET /api/comments/?project=1&root_only=true
```

### Créer un nouveau commentaire

```plaintext
POST /api/comments/
{
    "project": 1,
    "content": "Très intéressant comme projet ! J'aimerais en savoir plus sur la stratégie de développement."
}
```

### Répondre à un commentaire

```plaintext
POST /api/comments/
{
    "project": 1,
    "parent": 5,
    "content": "Merci pour votre intérêt ! Nous prévoyons de développer le projet en trois phases..."
}
```

### Modérer un commentaire

```plaintext
POST /api/comments/5/moderate/
{
    "is_approved": false
}
```

### Récupérer les commentaires en attente de modération

GET /api/comments/pending_moderation/
