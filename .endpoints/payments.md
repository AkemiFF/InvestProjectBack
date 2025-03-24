# Endpoints disponibles

Voici la liste des endpoints disponibles pour l'application "payments":

## Méthodes de paiement

- `GET /api/payments/methods/` - Liste des méthodes de paiement de l'utilisateur
- `POST /api/payments/methods/` - Ajouter une nouvelle méthode de paiement
- `GET /api/payments/methods/{id}/` - Détails d'une méthode de paiement spécifique
- `PUT /api/payments/methods/{id}/` - Mettre à jour une méthode de paiement
- `DELETE /api/payments/methods/{id}/` - Supprimer une méthode de paiement
- `POST /api/payments/methods/{id}/set_default/` - Définir une méthode de paiement comme méthode par défaut
- `GET /api/payments/methods/default/` - Récupérer la méthode de paiement par défaut de l'utilisateur

### Factures

- `GET /api/payments/invoices/` - Liste des factures de l'utilisateur
- `GET /api/payments/invoices/{id}/` - Détails d'une facture spécifique
- `GET /api/payments/invoices/pending/` - Récupérer les factures en attente de paiement
- `GET /api/payments/invoices/paid/` - Récupérer les factures payées
- `GET /api/payments/invoices/{id}/receipt/` - Générer un reçu pour une facture payée

### Traitement des paiements

- `POST /api/payments/process/process_payment/` - Traiter un paiement
- `GET /api/payments/process/transactions/` - Récupérer l'historique des transactions de l'utilisateur

## Exemples d'utilisation

### Ajouter une méthode de paiement

```plaintext
POST /api/payments/methods/
{
    "method_type": "credit_card",
    "provider": "Visa",
    "account_number": "4111111111111111",
    "expiry_date": "2025-12-31",
    "is_default": true
}
```

### Définir une méthode de paiement comme méthode par défaut

```plaintext
POST /api/payments/methods/3/set_default/
```

### Traiter un paiement

```plaintext
POST /api/payments/process/process_payment/
{
    "payment_method_id": 3,
    "invoice_id": 5
}
```

### Récupérer les factures en attente de paiement

```plaintext
GET /api/payments/invoices/pending/
```

### Générer un reçu pour une facture payée

```plaintext
GET /api/payments/invoices/5/receipt/
```

## Intégration avec d'autres applications

Pour intégrer les paiements avec d'autres applications, vous pouvez utiliser les fonctions utilitaires dans `payments/utils.py`. Par exemple, pour créer une facture lors de la création d'un abonnement:

```python
from payments.utils import create_invoice

def create_subscription(user, plan):
    # Créer l'abonnement
    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        status='pending',
        # ... autres champs
    )
    
    # Créer une facture pour l'abonnement
    invoice = create_invoice(
        user=user,
        amount=plan.price,
        description=f"Abonnement au plan {plan.name}",
        related_object=subscription,
        related_object_type='subscription'
    )
    
    return subscription, invoice
```

De même, pour créer une facture lors de la création d'un boost de projet:

```python
from payments.utils import create_invoice

def create_project_boost(user, project, days):
    # Calculer le montant
    amount_per_day = 5000
    amount = days * amount_per_day
    
    # Créer le boost
    boost = ProjectBoost.objects.create(
        project=project,
        days=days,
        amount_paid=amount,
        is_active=False,  # Sera activé après le paiement
        # ... autres champs
    )
    
    # Créer une facture pour le boost
    invoice = create_invoice(
        user=user,
        amount=amount,
        description=f"Boost du projet '{project.title}' pour {days} jours",
        related_object=boost,
        related_object_type='project_boost'
    )
    
    return boost, invoice
