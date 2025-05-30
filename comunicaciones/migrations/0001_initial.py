# Generated by Django 5.0.2 on 2025-05-25 05:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('colegios', '0003_delete_sede'),
        ('usuarios', '0005_remove_perfil_direccion_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mensaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenido', models.TextField()),
                ('leido', models.BooleanField(default=False)),
                ('fecha_envio', models.DateTimeField(auto_now_add=True)),
                ('colegio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes', to='colegios.colegio')),
                ('destinatario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes_recibidos', to='usuarios.perfil')),
                ('remitente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes_enviados', to='usuarios.perfil')),
            ],
            options={
                'ordering': ['-fecha_envio'],
            },
        ),
    ]
