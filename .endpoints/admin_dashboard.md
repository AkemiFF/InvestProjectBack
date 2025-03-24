# Endpoints disponibles

Voici la liste des endpoints disponibles pour l'application "admin_dashboard":

## Journaux d'administration

- `GET /api/admin/logs/` - Liste des journaux d'administration
- `GET /api/admin/logs/{id}/` - Détails d'un journal d'administration spécifique
- `GET /api/admin/logs/by_type/?type=user_management` - Liste des journaux par type d'action
- `GET /api/admin/logs/by_user/?user_id=1` - Liste des journaux par utilisateur

### Paramètres système

- `GET /api/admin/settings/` - Liste des paramètres système
- `POST /api/admin/settings/` - Ajouter un nouveau paramètre système
- `GET /api/admin/settings/{id}/` - Détails d'un paramètre système spécifique
- `PUT /api/admin/settings/{id}/` - Mettre à jour un paramètre système
- `DELETE /api/admin/settings/{id}/` - Supprimer un paramètre système
- `GET /api/admin/settings/public/` - Liste des paramètres système publics
- `GET /api/admin/settings/by_key/?key=site_name` - Récupérer un paramètre système par sa clé

### Statistiques

- `GET /api/admin/statistics/` - Liste des statistiques
- `GET /api/admin/statistics/{id}/` - Détails d'une statistique spécifique
- `GET /api/admin/statistics/by_type/?type=users&limit=30` - Liste des statistiques par type
- `GET /api/admin/statistics/by_date/?date=2023-01-01` - Liste des statistiques par date
- `POST /api/admin/statistics/update_daily/` - Mettre à jour les statistiques quotidiennes

### Tableau de bord

- `GET /api/admin/dashboard/metrics/` - Récupérer les métriques pour le tableau de bord
- `GET /api/admin/dashboard/user_growth/?period=month&limit=12` - Récupérer les données de croissance des utilisateurs
- `GET /api/admin/dashboard/revenue_data/?period=month&limit=12` - Récupérer les données de revenus

### Gestion des utilisateurs

- `GET /api/admin/users/list_users/?status=active&role=investor&search=john&page=1&page_size=10` - Liste des utilisateurs avec filtres
- `POST /api/admin/users/manage_user/` - Gérer un utilisateur (activation, désactivation, etc.)

### Gestion des projets

- `GET /api/admin/projects/list_projects/?status=pending&featured=true&hidden=false&search=eco&page=1&page_size=10` - Liste des projets avec filtres
- `POST /api/admin/projects/manage_project/` - Gérer un projet (approbation, rejet, etc.)

### Modération des commentaires

- `GET /api/admin/comments/list_reported_comments/?page=1&page_size=10` - Liste des commentaires signalés
- `POST /api/admin/comments/moderate_comment/` - Modérer un commentaire (approbation, rejet, etc.)

## Exemples d'utilisation

### Gérer un utilisateur

```plaintext
POST /api/admin/users/manage_user/
{
    "user_id": 5,
    "action": "deactivate",
    "reason": "Violation des conditions d'utilisation"
}
```

### Gérer un projet

```plaintext
POST /api/admin/projects/manage_project/
{
    "project_id": 3,
    "action": "approve",
    "reason": "Projet conforme aux directives"
}
```

### Modérer un commentaire

```plaintext
POST /api/admin/comments/moderate_comment/
{
    "comment_id": 12,
    "action": "reject",
    "reason": "Contenu inapproprié"
}
```

### Ajouter un paramètre système

```plaintext
POST /api/admin/settings/
{
    "key": "site_name",
    "value": "Plateforme de Crowdfunding",
    "description": "Nom du site affiché dans l'en-tête",
    "is_public": true
}
```

### Mettre à jour les statistiques quotidiennes

```plaintext
POST /api/admin/statistics/update_daily/
```

## Intégration avec d'autres applications

Pour intégrer le tableau de bord administratif avec d'autres applications, vous pouvez utiliser les fonctions utilitaires dans `admin_dashboard/utils.py`. Par exemple, pour enregistrer une action administrative:

```python
from admin_dashboard.utils import log_admin_action

def approve_project(request, project):
    # Approuver le projet
    project.status = 'approved'
    project.save()
    
    # Enregistrer l'action dans le journal d'administration
    log_admin_action(
        admin_user=request.user,
        action_type='project_validation',
        description=f"Approbation du projet '{project.title}'",
        related_object=project,
        ip_address=request.META.get('REMOTE_ADDR')
    )
