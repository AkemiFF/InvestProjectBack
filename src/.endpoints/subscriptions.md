# Endpoints disponibles

Voici la liste des endpoints disponibles pour l'application "subscriptions":

## Plans d'abonnement

- `GET /api/plans/` - Liste des plans d'abonnement disponibles
- `GET /api/plans/{id}/` - Détails d'un plan d'abonnement spécifique
- `GET /api/plans/by_type/?type=premium_investor` - Liste des plans d'abonnement par type

### Abonnements

- `GET /api/subscriptions/` - Liste des abonnements de l'utilisateur
- `GET /api/subscriptions/{id}/` - Détails d'un abonnement spécifique
- `POST /api/subscriptions/subscribe/` - S'abonner à un plan
- `POST /api/subscriptions/{id}/cancel/` - Annuler un abonnement
- `POST /api/subscriptions/{id}/renew/` - Renouveler un abonnement
- `GET /api/subscriptions/current/` - Récupérer l'abonnement actif de l'utilisateur
- `GET /api/subscriptions/history/` - Récupérer l'historique des abonnements de l'utilisateur
- `GET /api/subscriptions/status/` - Vérifier le statut de l'abonnement de l'utilisateur

### Boosts de projets

- `GET /api/boosts/` - Liste des boosts de projets de l'utilisateur
- `GET /api/boosts/{id}/` - Détails d'un boost de projet spécifique
- `POST /api/boosts/boost_project/` - Booster un projet
- `POST /api/boosts/{id}/cancel/` - Annuler un boost de projet
- `GET /api/boosts/active/` - Récupérer les boosts actifs de l'utilisateur
- `GET /api/boosts/history/` - Récupérer l'historique des boosts de l'utilisateur
- `GET /api/boosts/project_boosts/?project_id=1` - Récupérer les boosts d'un projet spécifique

## Exemples d'utilisation

### S'abonner à un plan

```plaintext
POST /api/subscriptions/subscribe/
{
    "plan_id": 2,
    "auto_renew": true
}
```

### Annuler un abonnement

```plaintext
POST /api/subscriptions/5/cancel/
```

### Renouveler un abonnement

```plaintext
POST /api/subscriptions/5/renew/
{
    "auto_renew": true
}
```

### Vérifier le statut de l'abonnement

```plaintext
GET /api/subscriptions/status/
```

### Booster un projet

```plaintext
POST /api/boosts/boost_project/
{
    "project_id": 3,
    "days": 7
}
```

### Récupérer les boosts actifs

```plaintext
GET /api/boosts/active/
```

## Intégration avec d'autres applications

Pour intégrer les abonnements avec d'autres applications, vous pouvez utiliser les fonctions utilitaires dans `subscriptions/utils.py`. Par exemple, pour vérifier le type d'abonnement d'un utilisateur avant d'autoriser certaines fonctionnalités:

```python
from subscriptions.utils import get_user_subscription_type

def check_premium_features(user):
    subscription_type = get_user_subscription_type(user)
    
    if subscription_type == 'basic':
        # Fonctionnalités de base
        return False
    elif subscription_type == 'premium_investor':
        # Fonctionnalités premium pour investisseurs
        return True
    elif subscription_type == 'premium_project_owner':
        # Fonctionnalités premium pour porteurs de projet
        return True
```

Vous pouvez également vérifier si un projet est boosté:

```python
from subscriptions.utils import check_project_boost_status

def get_project_visibility(project):
    boost = check_project_boost_status(project)
    
    if boost:
        # Le projet est boosté, lui donner une visibilité accrue
        return "high"
    else:
        # Visibilité normale
        return "normal"
