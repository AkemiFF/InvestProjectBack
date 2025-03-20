# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from .models import InvestorProfile, ProjectOwnerProfile, Favorite

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'user_type')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Un utilisateur avec cet email existe déjà."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user_type = validated_data.pop('user_type')
        
        user = User.objects.create_user(**validated_data)
        user.user_type = user_type
        user.save()
        
        # Créer le profil correspondant au type d'utilisateur
        if user_type == 'investor':
            InvestorProfile.objects.create(user=user)
        elif user_type == 'project_owner':
            ProjectOwnerProfile.objects.create(user=user)
        
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not (username or email):
            raise serializers.ValidationError(_("Vous devez fournir un nom d'utilisateur ou un email."))
        
        if email:
            try:
                username = User.objects.get(email=email).username
            except User.DoesNotExist:
                raise serializers.ValidationError(_("Aucun utilisateur trouvé avec cet email."))
        
        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError(_("Identifiants invalides."))
        
        if not user.is_active:
            raise serializers.ValidationError(_("Ce compte a été désactivé."))
        
        attrs['user'] = user
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'user_type', 
                  'profile_picture', 'biography', 'phone_number', 'email_verified', 'date_joined')
        read_only_fields = ('id', 'email', 'user_type', 'email_verified', 'date_joined')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Les mots de passe ne correspondent pas."})
        return attrs

class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class ResetPasswordConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Les mots de passe ne correspondent pas."})
        return attrs

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)

class InvestorProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = InvestorProfile
        fields = ('user', 'investment_domain', 'total_invested', 'balance', 'projects_supported')
        read_only_fields = ('total_invested', 'balance', 'projects_supported')

class ProjectOwnerProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = ProjectOwnerProfile
        fields = ('user', 'active_campaigns', 'funded_projects', 'balance')
        read_only_fields = ('active_campaigns', 'funded_projects', 'balance')

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'project', 'project_owner', 'date_added')
        read_only_fields = ('id', 'user', 'date_added')

class SocialAuthSerializer(serializers.Serializer):
    provider = serializers.CharField(required=True)
    access_token = serializers.CharField(required=True)