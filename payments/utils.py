# payments/utils.py
from django.utils import timezone
from .models import Invoice
import uuid

def generate_invoice_number():
    """
    Génère un numéro de facture unique
    """
    prefix = "INV"
    date_part = timezone.now().strftime("%Y%m%d")
    random_part = str(uuid.uuid4().int)[:6]
    return f"{prefix}-{date_part}-{random_part}"

def create_invoice(user, amount, description, related_object=None, related_object_type=None):
    """
    Crée une nouvelle facture
    """
    invoice_number = generate_invoice_number()
    issue_date = timezone.now().date()
    due_date = issue_date + timezone.timedelta(days=7)  # Par défaut, la facture est due dans 7 jours
    
    invoice = Invoice.objects.create(
        user=user,
        invoice_number=invoice_number,
        amount=amount,
        description=description,
        status='sent',
        issue_date=issue_date,
        due_date=due_date
    )
    
    # Si un objet lié est fourni, l'associer à la facture
    if related_object and related_object_type:
        invoice.related_object_id = related_object.id
        invoice.related_object_type = related_object_type
        invoice.save(update_fields=['related_object_id', 'related_object_type'])
    
    return invoice

def get_user_transactions(user):
    """
    Récupère toutes les transactions d'un utilisateur
    """
    # Récupérer toutes les factures de l'utilisateur
    invoices = Invoice.objects.filter(user=user).order_by('-issue_date')
    
    transactions = []
    
    for invoice in invoices:
        transaction = {
            'id': str(uuid.uuid4()),
            'type': 'payment',
            'amount': invoice.amount,
            'date': invoice.paid_date if invoice.status == 'paid' else invoice.issue_date,
            'status': invoice.status,
            'description': invoice.description,
            'invoice': invoice,
            'payment_method': 'Non spécifié'  # Dans un système réel, vous récupéreriez la méthode de paiement utilisée
        }
        
        transactions.append(transaction)
    
    return transactions

def generate_receipt_data(invoice):
    """
    Génère les données pour un reçu de paiement
    """
    if invoice.status != 'paid':
        return None
    
    receipt_data = {
        'receipt_number': f"REC-{invoice.invoice_number[4:]}",
        'invoice_number': invoice.invoice_number,
        'date': invoice.paid_date,
        'customer': {
            'name': invoice.user.get_full_name() or invoice.user.username,
            'email': invoice.user.email,
            'address': getattr(invoice.user, 'address', 'Non spécifié')
        },
        'amount': invoice.amount,
        'description': invoice.description,
        'payment_method': 'Non spécifié'  # Dans un système réel, vous récupéreriez la méthode de paiement utilisée
    }
    
    return receipt_data