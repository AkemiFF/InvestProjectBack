from investments.models import Transaction
from rest_framework import serializers

from .models import Wallet, WalletTransaction


class WalletSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'updated_at']
        read_only_fields = ['id', 'balance', 'updated_at']
        
    def get_balance(self, obj):
        # Retourne un dictionnaire avec amount et currency
        return {
            'amount': str(obj.balance.amount),
            'currency': str(obj.balance.currency)
        }

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'transaction_type', 'amount', 'created_at',"status"]
        read_only_fields = ['id', 'transaction_type', 'amount', 'created_at']

class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'status', 'created_at', 'completed_at']
        read_only_fields = ['id', 'status', 'created_at', 'completed_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['transaction_type'] = 'deposit'
        return Transaction.objects.create(**validated_data)

class WithdrawalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    currency = serializers.CharField(max_length=3, required=False, default='EUR')
    account_number = serializers.CharField(max_length=50, required=False)
    bank_code = serializers.CharField(max_length=20, required=False)
    account_name = serializers.CharField(max_length=100, required=False)

class CurrencySerializer(serializers.Serializer):
    currency = serializers.CharField(max_length=3)
