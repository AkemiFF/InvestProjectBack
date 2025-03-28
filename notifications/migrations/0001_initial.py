# Generated by Django 5.1.7 on 2025-03-20 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('comment', 'Nouveau commentaire'), ('reply', 'Réponse à un commentaire'), ('message', 'Nouveau message'), ('investment', 'Nouvel investissement'), ('project_update', 'Mise à jour de projet'), ('system', 'Notification système')], max_length=20)),
                ('title', models.CharField(max_length=100)),
                ('message', models.TextField()),
                ('related_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('related_object_type', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
