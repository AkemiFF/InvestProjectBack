# users/views.py
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import InvestorProfile, ProjectOwnerProfile, Favorite
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, ResetPasswordRequestSerializer, ResetPasswordConfirmSerializer,
    EmailVerificationSerializer, InvestorProfileSerializer, ProjectOwnerProfileSerializer,
    FavoriteSerializer, SocialAuthSerializer
)
from .permissions import IsOwnerOrAdmin
from .utils import send_verification_email, send_password_reset_email, verify_token

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint pour l'inscription des utilisateurs
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Envoyer l'email de vérification
        send_verification_email(user)
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)

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