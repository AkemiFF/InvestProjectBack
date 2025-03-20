# users/views.py
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
# views.py ou un service d'email de vérification
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .models import (Favorite, InvestorProfile, ProjectOwnerProfile,
                     RegistrationRequest)
from .permissions import IsOwnerOrAdmin
from .serializers import *
from .utils import (send_password_reset_email, send_verification_email,
                    verify_token)

User = get_user_model()

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def initiate_registration2(request):
    # print("Corps de la requête reçu :", request.data)  # Décode le corps brut en chaîne de caractères
    serializer = InitiateRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    email = User.objects.normalize_email(serializer.validated_data['email'])
    
    # Vérifier si l'email existe déjà
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email déjà enregistré"}, status=400)
    
    # Générer un code de 6 chiffres
    code = ''.join(secrets.choice(string.digits) for _ in range(6))
    
    # Créer ou mettre à jour la demande d'inscription
    RegistrationRequest.objects.update_or_create(
        email=email,
        defaults={'code': code, 'created_at': timezone.now()}
    )
    
    # Envoyer le code par email (à remplacer par une tâche asynchrone en production)
    send_mail(
        'Votre code de vérification NexusInvest',
        f'Votre code de vérification est : {code}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    
    return Response({"message": "Code de vérification envoyé par email"})


def send_link_email(user):
    """
    Fonction pour envoyer un email de vérification à l'utilisateur
    """
    signer = TimestampSigner()
    token = signer.sign(user.id)
    
    frontend_url = settings.NEXT_PUBLIC_FRONTEND_URL
    verification_link = f"{frontend_url}/auth/verify-token?token={token}"
    
    subject = "Vérification de votre adresse email"
    message = (
        "Bonjour,\n\n"
        "Nous avons envoyé un lien de vérification à votre adresse email.\n"
        "Veuillez cliquer sur le lien suivant pour vérifier votre compte :\n"
        f"{verification_link}\n\n"
        "Si vous n'avez pas créé de compte, ignorez cet email.\n"
    )
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def initiate_registration(request):
    
    serializer = CompleteRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    email = User.objects.normalize_email(serializer.validated_data['email'])
    name = serializer.validated_data['name']
    password = serializer.validated_data['password']
    user_type = serializer.validated_data['userType']
    
    # Vérifier si le nom d'utilisateur est déjà pris
    if User.objects.filter(username=name).exists():
        return Response({"error": "Nom d'utilisateur déjà pris"}, status=406)
    # Remplacer les espaces par des underscores dans le nom d'utilisateur
    name = name.replace(" ", "_")
    # Créer l'utilisateur
    try:
        user = User.objects.create_user(
            email=email,
            username=name,
            password=password,
            user_type=user_type,
            is_active=False  # Désactivé jusqu'à la vérification par email
        )
        send_link_email(user)  # Envoyer l'email de confirmation
    except IntegrityError:
        return Response({"error": "Erreur lors de la création du compte"}, status=400)

    return Response({
        "message": "Compte créé avec succès",
        "user_id": user.id,
        "email": user.email,
        "username": user.username
    }, status=201)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def complete_registration(request):
    token = request.data.get("token")
    signer = TimestampSigner()
    try:
        user_id = signer.unsign(token, max_age=3600) 
    except SignatureExpired:
        return JsonResponse({"detail": "Token expiré"}, status=401)
    except BadSignature:
        return JsonResponse({"detail": "Token invalide"}, status=401)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"detail": "Utilisateur introuvable"}, status=404)
    
    user.is_active = True
    user.save()
    return JsonResponse({"detail": "Email vérifié avec succès"}, status=200)

class UserLoginView(APIView):
    """
    API endpoint pour la connexion des utilisateurs
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user).data
        })

class EmailVerificationView(APIView):
    """
    API endpoint pour la vérification des emails
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        
        user = verify_token(uid, token)
        
        if user is None:
            return Response(
                {"detail": "Le lien de vérification est invalide ou a expiré."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.email_verified = True
        user.save()
        
        return Response({"detail": "Votre email a été vérifié avec succès."})

class ResetPasswordRequestView(APIView):
    """
    API endpoint pour demander la réinitialisation du mot de passe
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user)
            return Response({"detail": "Un email de réinitialisation a été envoyé."})
        except User.DoesNotExist:
            # Pour des raisons de sécurité, ne pas indiquer si l'email existe ou non
            return Response({"detail": "Un email de réinitialisation a été envoyé."})

class ResetPasswordConfirmView(APIView):
    """
    API endpoint pour confirmer la réinitialisation du mot de passe
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        user = verify_token(uid, token)
        
        if user is None:
            return Response(
                {"detail": "Le lien de réinitialisation est invalide ou a expiré."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({"detail": "Votre mot de passe a été réinitialisé avec succès."})

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les utilisateurs
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        # Les utilisateurs normaux ne peuvent voir que leur propre profil
        if not self.request.user.is_staff:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Récupérer le profil de l'utilisateur connecté
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Mettre à jour le profil de l'utilisateur connecté
        """
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Changer le mot de passe de l'utilisateur connecté
        """
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Vérifier l'ancien mot de passe
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"old_password": ["Le mot de passe actuel est incorrect."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Définir le nouveau mot de passe
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({"detail": "Mot de passe modifié avec succès."})
    
    @action(detail=False, methods=['post'])
    def upload_profile_picture(self, request):
        """
        Télécharger une photo de profil
        """
        user = request.user
        
        if 'profile_picture' not in request.FILES:
            return Response(
                {"detail": "Aucune image fournie."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.profile_picture = request.FILES['profile_picture']
        user.save()
        
        return Response({"detail": "Photo de profil mise à jour avec succès."})

class InvestorProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les profils d'investisseurs
    """
    queryset = InvestorProfile.objects.all()
    serializer_class = InvestorProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        # Les utilisateurs normaux ne peuvent voir que leur propre profil
        if not self.request.user.is_staff:
            return InvestorProfile.objects.filter(user=self.request.user)
        return InvestorProfile.objects.all()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Récupérer le profil d'investisseur de l'utilisateur connecté
        """
        try:
            profile = InvestorProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except InvestorProfile.DoesNotExist:
            return Response(
                {"detail": "Vous n'avez pas de profil d'investisseur."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Mettre à jour le profil d'investisseur de l'utilisateur connecté
        """
        try:
            profile = InvestorProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except InvestorProfile.DoesNotExist:
            return Response(
                {"detail": "Vous n'avez pas de profil d'investisseur."},
                status=status.HTTP_404_NOT_FOUND
            )

class ProjectOwnerProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les profils de porteurs de projet
    """
    queryset = ProjectOwnerProfile.objects.all()
    serializer_class = ProjectOwnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        # Les utilisateurs normaux ne peuvent voir que leur propre profil
        if not self.request.user.is_staff:
            return ProjectOwnerProfile.objects.filter(user=self.request.user)
        return ProjectOwnerProfile.objects.all()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Récupérer le profil de porteur de projet de l'utilisateur connecté
        """
        try:
            profile = ProjectOwnerProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except ProjectOwnerProfile.DoesNotExist:
            return Response(
                {"detail": "Vous n'avez pas de profil de porteur de projet."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """
        Mettre à jour le profil de porteur de projet de l'utilisateur connecté
        """
        try:
            profile = ProjectOwnerProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except ProjectOwnerProfile.DoesNotExist:
            return Response(
                {"detail": "Vous n'avez pas de profil de porteur de projet."},
                status=status.HTTP_404_NOT_FOUND
            )

class SocialAuthView(APIView):
    """
    API endpoint pour l'authentification sociale
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        provider = serializer.validated_data['provider']
        access_token = serializer.validated_data['access_token']
        
        # Ici, vous devriez implémenter la logique pour vérifier le token avec le fournisseur
        # et récupérer les informations de l'utilisateur
        # Cela dépend des bibliothèques que vous utilisez (social-auth-app-django, etc.)
        
        # Pour cet exemple, nous allons simplement retourner une erreur
        return Response(
            {"detail": "L'authentification sociale n'est pas encore implémentée."},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that adds additional information to the response.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            # Add user info to response
            email = request.data.get('email')
            password = request.data.get('password')
            user = authenticate(email=email, password=password)
            if user is None:
                return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            response.data['user_id'] = user.id
            response.data['username'] = user.username
            response.data['email'] = user.email
            response.data['role'] = user.user_type
            response.data['pic'] = user.profile_picture
            
            # Add token expiration info
            response.data['token_lifetime'] = {
                'access': settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                'refresh':settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
            }
        
        return response
    
class CustomRefresh(TokenRefreshView):
    """
    Custom refresh view that returns additional user information and token lifetime details,
    similar to CustomTokenObtainPairView.
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            refresh_token = request.data.get("refresh")
            try:
                token = RefreshToken(refresh_token)
                user_id = token.get("user_id")
                User = get_user_model()
                user = User.objects.get(id=user_id)
            except Exception as e:
                return Response({"detail": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
            
            response.data['user_id'] = user.id
            response.data['username'] = user.username
            response.data['email'] = user.email
            response.data['role'] = getattr(user, "user_type", None)
            response.data['token_lifetime'] = {
                'access': settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                'refresh': settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            }
        
        return response