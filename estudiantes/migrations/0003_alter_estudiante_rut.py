# Generated by Django 5.0.2 on 2025-06-06 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estudiantes', '0002_alter_estudiante_options_alter_estudiante_curso_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='estudiante',
            name='rut',
            field=models.CharField(max_length=9, unique=True),
        ),
    ]
