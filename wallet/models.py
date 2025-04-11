from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from djmoney.models.fields import MoneyField
from investments.models import Investment, Transaction
from users.models import User

# Create your models here.

def convert_currency(amount, from_currency, to_currency):
    exchange_rates = {
        'EUR': Decimal('1.0'),
        'USD': Decimal('1.1'), 
        'MGA': Decimal('4800.0'),  
    }
    
    try:
        amount = Decimal(amount)
    except (InvalidOperation, ValueError):
        raise ValueError("Le montant doit être un nombre valide.")
    
    try:
        # Convertir le montant en unité de la devise de référence (EUR)
        base_amount = amount / exchange_rates[from_currency]
        # Convertir de la devise de référence vers la devise cible
        converted_amount = base_amount * exchange_rates[to_currency]
    except KeyError:
        raise ValueError("Devise non prise en charge. Vérifiez les codes devises.")
    
    # Retourner le résultat arrondi à 2 décimales
    return converted_amount.quantize(Decimal('0.01'))


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = MoneyField(max_digits=12, decimal_places=2, default_currency='EUR')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet of {self.user.username} - Balance: {self.balance}"

    def deposit(self, amount):
        """Ajouter des fonds au portefeuille"""
        self.balance += amount
        self.save()

    def invest_with_wallet(user, project, amount):
        wallet = user.wallet
        if wallet.withdraw(amount):  # Vérifie si le portefeuille a suffisamment de fonds
            investment = Investment.objects.create(
                user=user,
                project=project,
                amount=amount,
                status='completed',
                payment_method='wallet'
            )
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='investment',
                amount=amount
            )
            return investment
        else:
            raise ValueError("Fonds insuffisants dans le portefeuille.")
        
    def withdraw(self, amount, currency=None):
        if amount <= 0:
            raise ValidationError("Le montant doit être positif.")
        
        # Si une devise différente est passée, ou en cas de logique de conversion, la gérer ici
        if currency and currency != self.balance.currency.code:
            # Conversion sécurisée – à implémenter selon votre stratégie de conversion
            amount = convert_currency(amount, from_currency=currency, to_currency=self.balance.currency.code)
        
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)
            if wallet.balance.amount < amount:
                raise ValidationError("Solde insuffisant.")
            wallet.balance -= amount
            wallet.save()
            # Enregistrer la transaction
            Transaction.objects.create(wallet=wallet, transaction_type='WITHDRAWAL', amount=amount)
            return True
        return False


class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Dépôt'),
        ('withdraw', 'Retrait'),
        ('investment', 'Investissement'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} - {self.amount} - {self.wallet.user.username}"
