from investments.models import Transaction
from rest_framework import serializers

from .models import Wallet, WalletTransaction


class WalletSerializer(serializers.ModelSerializer):
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
        fields = ['id', 'transaction_type', 'amount', 'created_at']
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
