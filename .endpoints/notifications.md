# Endpoints disponibles

Voici la liste des endpoints disponibles pour l'application "notifications":

## Notifications

- `GET /api/notifications/` - Liste des notifications de l'utilisateur connecté
- `GET /api/notifications/{id}/` - Détails d'une notification spécifique
- `DELETE /api/notifications/{id}/` - Supprimer une notification
- `POST /api/notifications/{id}/mark_as_read/` - Marquer une notification comme lue
- `POST /api/notifications/mark_all_as_read/` - Marquer toutes les notifications comme lues
- `GET /api/notifications/unread_count/` - Récupérer le nombre de notifications non lues
- `DELETE /api/notifications/delete_all_read/` - Supprimer toutes les notifications lues

## Paramètres de filtrage pour les notifications

- `type` - Filtrer par type de notification (comment, reply, investment, project_update, system)
- `is_read` - Filtrer par statut de lecture (true/false)

## Exemples d'utilisation

### Récupérer toutes les notifications non lues

```plaintext
GET /api/notifications/?is_read=false
```

### Récupérer les notifications d'un type spécifique

```plaintext
GET /api/notifications/?type=comment
```

### Marquer une notification comme lue

```plaintext
POST /api/notifications/5/mark_as_read/
```

### Marquer toutes les notifications comme lues

```plaintext
POST /api/notifications/mark_all_as_read/
```

### Récupérer le nombre de notifications non lues

```plaintext
GET /api/notifications/unread_count/
```

### Supprimer toutes les notifications lues

```plaintext
DELETE /api/notifications/delete_all_read/
```

## Intégration avec d'autres applications

Pour intégrer les notifications avec d'autres applications, vous pouvez utiliser les fonctions utilitaires dans `notifications/utils.py`. Par exemple, pour créer une notification lorsqu'un utilisateur commente un projet:

```python
# Dans comments/views.py

from notifications.utils import create_comment_notification

class CommentViewSet(viewsets.ModelViewSet):
    # ...
    
    def perform_create(self, serializer):
        comment = serializer.save()
        
        # Créer une notification pour le propriétaire du projet
        project = comment.project
        if comment.author != project.owner:
            create_comment_notification(
                project_owner=project.owner,
                commenter=comment.author,
                project=project,
                comment=comment
            )
