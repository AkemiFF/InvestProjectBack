# Generated by Django 5.1.7 on 2025-03-20 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('user_management', 'Gestion utilisateur'), ('project_validation', 'Validation de projet'), ('comment_moderation', 'Modération de commentaire'), ('payment_management', 'Gestion de paiement'), ('system_config', 'Configuration système'), ('other', 'Autre')], max_length=30)),
                ('description', models.TextField()),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('related_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('related_object_type', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Statistic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stat_type', models.CharField(choices=[('users', 'Utilisateurs'), ('projects', 'Projets'), ('investments', 'Investissements'), ('revenue', 'Revenus'), ('visits', 'Visites'), ('other', 'Autre')], max_length=20)),
                ('value', models.DecimalField(decimal_places=2, max_digits=15)),
                ('date', models.DateField()),
                ('description', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SystemSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True)),
                ('value', models.TextField()),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
