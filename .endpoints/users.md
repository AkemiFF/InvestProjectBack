# Endpoints disponibles

Voici la liste des endpoints disponibles pour l'application "users":

## Authentification

- `POST /api/auth/register/` - Inscription d'un nouvel utilisateur
- `POST /api/auth/login/` - Connexion d'un utilisateur
- `POST /api/auth/verify-email/` - Vérification de l'adresse email
- `POST /api/auth/reset-password-request/` - Demande de réinitialisation du mot de passe
- `POST /api/auth/reset-password-confirm/` - Confirmation de la réinitialisation du mot de passe
- `POST /api/auth/social/` - Authentification via un réseau social

### Gestion des utilisateurs

- `GET /api/users/me/` - Récupérer le profil de l'utilisateur connecté
- `PUT /api/users/update_profile/` - Mettre à jour le profil de l'utilisateur connecté
- `PATCH /api/users/update_profile/` - Mettre à jour partiellement le profil de l'utilisateur connecté
- `POST /api/users/change_password/` - Changer le mot de passe de l'utilisateur connecté
- `POST /api/users/upload_profile_picture/` - Télécharger une photo de profil

### Profils d'investisseurs

- `GET /api/investor-profiles/me/` - Récupérer le profil d'investisseur de l'utilisateur connecté
- `PUT /api/investor-profiles/update_profile/` - Mettre à jour le profil d'investisseur
- `PATCH /api/investor-profiles/update_profile/` - Mettre à jour partiellement le profil d'investisseur

### Profils de porteurs de projet

- `GET /api/project-owner-profiles/me/` - Récupérer le profil de porteur de projet de l'utilisateur connecté
- `PUT /api/project-owner-profiles/update_profile/` - Mettre à jour le profil de porteur de projet
- `PATCH /api/project-owner-profiles/update_profile/` - Mettre à jour partiellement le profil de porteur de projet

## Exemples d'utilisation

### Inscription d'un nouvel utilisateur

```plaintext
POST /api/auth/register/
{
    "username": "john_doe",
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!",
    "user_type": "investor"
}
```

### Connexion d'un utilisateur

```plaintext
POST /api/auth/login/
{
    "email": "john.doe@example.com",
    "password": "SecurePassword123!"
}
```

### Vérification de l'adresse email

```plaintext
POST /api/auth/verify-email/
{
    "token": "token-reçu-par-email",
    "uid": "uid-reçu-par-email"
}
```

### Demande de réinitialisation du mot de passe

```plaintext
POST /api/auth/reset-password-request/
{
    "email": "john.doe@example.com"
}
```

### Confirmation de la réinitialisation du mot de passe

```plaintext
POST /api/auth/reset-password-confirm/
{
    "token": "token-reçu-par-email",
    "uid": "uid-reçu-par-email",
    "new_password": "NouveauMotDePasse123!",
    "confirm_password": "NouveauMotDePasse123!"
}
```

### Mise à jour du profil utilisateur

```plaintext
PUT /api/users/update_profile/
{
    "first_name": "John",
    "last_name": "Smith",
    "biography": "Investisseur passionné par les projets innovants.",
    "phone_number": "+33612345678"
}
```

### Changement de mot de passe

```plaintext
POST /api/users/change_password/
{
    "old_password": "AncienMotDePasse123!",
    "new_password": "NouveauMotDePasse123!",
    "confirm_password": "NouveauMotDePasse123!"
}
```

### Mise à jour du profil d'investisseur

PATCH /api/investor-profiles/update_profile/
{
    "investment_domain": "Technologies, Santé, Environnement"
}
