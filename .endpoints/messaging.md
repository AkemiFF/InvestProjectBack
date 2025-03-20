# Endpoints disponibles

Voici la liste des endpoints disponibles pour l'application "messaging":

## Conversations

- `GET /api/conversations/` - Liste des conversations de l'utilisateur connecté
- `GET /api/conversations/{id}/` - Détails d'une conversation spécifique
- `DELETE /api/conversations/{id}/` - Supprimer une conversation
- `POST /api/conversations/start/` - Démarrer une nouvelle conversation ou utiliser une existante
- `GET /api/conversations/{id}/messages/` - Récupérer les messages d'une conversation
- `POST /api/conversations/{id}/mark_as_read/` - Marquer tous les messages non lus d'une conversation comme lus
- `GET /api/conversations/unread_count/` - Récupérer le nombre total de messages non lus

### Messages

- `GET /api/messages/` - Liste des messages des conversations de l'utilisateur
- `POST /api/messages/` - Envoyer un nouveau message
- `GET /api/messages/{id}/` - Détails d'un message spécifique
- `DELETE /api/messages/{id}/` - Supprimer un message
- `POST /api/messages/{id}/mark_as_read/` - Marquer un message comme lu

## Exemples d'utilisation

### Démarrer une nouvelle conversation

POST /api/conversations/start/
{
    "recipient_id": 2,
    "message": "Bonjour, je suis intéressé par votre projet. Pouvez-vous me donner plus d'informations ?"
}

### Récupérer les messages d'une conversation

GET /api/conversations/1/messages/

### Envoyer un message dans une conversation existante

POST /api/messages/
{
    "conversation": 1,
    "content": "Merci pour ces informations. J'aimerais investir dans votre projet."
}

### Marquer tous les messages d'une conversation comme lus

POST /api/conversations/1/mark_as_read/

### Récupérer le nombre total de messages non lus

GET /api/conversations/unread_count/
