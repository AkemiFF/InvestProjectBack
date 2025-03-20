# Endpoints disponibles

Voici la liste des endpoints disponibles pour l'application "investments":

## Investissements

- `GET /api/investments/` - Liste des investissements (filtrés selon l'utilisateur)
- `POST /api/investments/` - Créer un nouvel investissement
- `GET /api/investments/{id}/` - Détails d'un investissement spécifique
- `DELETE /api/investments/{id}/` - Supprimer un investissement (admin uniquement)
- `POST /api/investments/{id}/cancel/` - Annuler un investissement en attente
- `POST /api/investments/{id}/confirm/` - Confirmer un investissement (admin uniquement)
- `GET /api/investments/my_investments/` - Liste des investissements de l'utilisateur connecté
- `GET /api/investments/project_investments/` - Liste des investissements pour les projets de l'utilisateur
- `GET /api/investments/statistics/` - Statistiques sur les investissements de l'utilisateur

### Transactions

- `GET /api/transactions/` - Liste des transactions de l'utilisateur
- `GET /api/transactions/{id}/` - Détails d'une transaction spécifique
- `POST /api/transactions/deposit/` - Effectuer un dépôt
- `POST /api/transactions/withdraw/` - Effectuer un retrait
- `GET /api/transactions/balance/` - Récupérer le solde de l'utilisateur

## Paramètres de filtrage pour les investissements

- `status` - Filtrer par statut (pending, completed, cancelled, refunded)
- `project` - Filtrer par ID de projet

## Paramètres de filtrage pour les transactions

- `transaction_type` - Filtrer par type de transaction (deposit, withdrawal, investment, commission, refund)
- `status` - Filtrer par statut (pending, completed, failed)

## Exemples d'utilisation

### Créer un nouvel investissement

```plaintext
POST /api/investments/
{
    "project_id": 1,
    "amount": 50000,
    "notes": "Je crois en ce projet et souhaite contribuer à son succès."
}
```

### Récupérer les investissements de l'utilisateur

```plaintext
GET /api/investments/my_investments/
```

### Annuler un investissement en attente

```plaintext
POST /api/investments/5/cancel/
```

### Effectuer un dépôt

```plaintext
POST /api/transactions/deposit/
{
    "amount": 100000,
    "payment_method": "Carte bancaire"
}
```

### Effectuer un retrait

```plaintext
POST /api/transactions/withdraw/
{
    "amount": 50000,
    "bank_details": "IBAN: MG46..."
}
```

### Récupérer le solde de l'utilisateur

```plaintext
GET /api/transactions/balance/
```

## Intégration avec d'autres applications

Pour intégrer les investissements avec d'autres applications, vous pouvez utiliser les fonctions utilitaires dans `investments/utils.py`. Par exemple, pour mettre à jour les statistiques d'un utilisateur après un investissement:

```python
from investments.utils import update_user_investment_stats, update_project_owner_stats

# Mettre à jour les statistiques de l'investisseur
update_user_investment_stats(investor)

# Mettre à jour les statistiques du porteur de projet
update_project_owner_stats(project_owner)
