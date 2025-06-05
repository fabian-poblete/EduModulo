from django.shortcuts import render
import os
import json
import shutil
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse
from django.conf import settings
from django.contrib import messages
from .models import Backup
import subprocess
from django.core import serializers
from django.db import transaction
import codecs
import chardet


def is_superuser(user):
    return user.is_superuser


@login_required
@user_passes_test(is_superuser)
def backup_list(request):
    """List all backups"""
    backups = Backup.objects.all()
    return render(request, 'system_backup/backup_list.html', {
        'backups': backups
    })


@login_required
@user_passes_test(is_superuser)
def create_backup(request):
    """Create a new backup"""
    try:
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Generate timestamp for backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_{timestamp}'
        backup_path = os.path.join(backup_dir, backup_name)

        # Create backup directory
        os.makedirs(backup_path)

        # Backup database with explicit encoding
        db_backup_path = os.path.join(backup_path, 'db_backup.json')
        try:
            subprocess.run(
                f'python manage.py dumpdata --exclude contenttypes --exclude auth.permission --indent 2 -o {db_backup_path}',
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )
        except subprocess.CalledProcessError as e:
            raise Exception(
                f'Error al crear el respaldo de la base de datos: {e.stderr}')

        # Backup media files
        media_backup_path = os.path.join(backup_path, 'media')
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.copytree(settings.MEDIA_ROOT, media_backup_path)

        # Create backup info file
        backup_info = {
            'timestamp': timestamp,
            'database': 'db_backup.json',
            'media': 'media' if os.path.exists(settings.MEDIA_ROOT) else None
        }

        with open(os.path.join(backup_path, 'backup_info.json'), 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)

        # Create backup record in database
        backup = Backup.objects.create(
            name=backup_name,
            size=get_dir_size(backup_path),
            status='success',
            description='Respaldo automático del sistema'
        )

        messages.success(request, 'Respaldo creado exitosamente')
    except Exception as e:
        messages.error(request, f'Error al crear el respaldo: {str(e)}')

    return redirect('system_backup:backup_list')


@login_required
@user_passes_test(is_superuser)
def download_backup(request, backup_id):
    """Download a backup file"""
    try:
        backup = get_object_or_404(Backup, id=backup_id)
        backup_path = backup.get_backup_path()

        if not os.path.exists(backup_path):
            messages.error(request, 'Respaldo no encontrado')
            return redirect('system_backup:backup_list')

        # Create a zip file of the backup
        shutil.make_archive(backup_path, 'zip', backup_path)

        # Return the zip file
        response = FileResponse(
            open(backup.get_zip_path(), 'rb'),
            as_attachment=True,
            filename=f'{backup.name}.zip'
        )
        return response
    except Exception as e:
        messages.error(request, f'Error al descargar el respaldo: {str(e)}')
        return redirect('system_backup:backup_list')


@login_required
@user_passes_test(is_superuser)
def restore_backup(request, backup_id):
    """Restore a backup"""
    try:
        backup = get_object_or_404(Backup, id=backup_id)
        backup_path = backup.get_backup_path()

        if not os.path.exists(backup_path):
            messages.error(request, 'Respaldo no encontrado')
            return redirect('system_backup:backup_list')

        # Restore database
        db_backup_path = backup.get_db_backup_path()
        if not os.path.exists(db_backup_path):
            messages.error(
                request, 'Archivo de respaldo de la base de datos no encontrado')
            return redirect('system_backup:backup_list')

        # Verify backup file is not empty
        if os.path.getsize(db_backup_path) == 0:
            messages.error(request, 'El archivo de respaldo está vacío')
            return redirect('system_backup:backup_list')

        # Create a temporary backup of current database
        temp_backup_path = os.path.join(
            settings.BASE_DIR, 'backups', 'temp_backup.json')
        try:
            subprocess.run(
                f'python manage.py dumpdata --exclude contenttypes --exclude auth.permission --indent 2 -o {temp_backup_path}',
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )
        except subprocess.CalledProcessError as e:
            messages.error(
                request, f'Error al crear el respaldo temporal: {e.stderr}')
            return redirect('system_backup:backup_list')

        try:
            # Convert backup file to UTF-8
            # Detect the encoding of the file
            with open(db_backup_path, 'rb') as file:
                raw_data = file.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding']

            # Read the file with detected encoding and convert to UTF-8
            with codecs.open(db_backup_path, 'r', encoding=encoding, errors='replace') as file:
                content = file.read()

            # Write the content back in UTF-8
            with codecs.open(db_backup_path, 'w', encoding='utf-8') as file:
                file.write(content)

            # Now read and process the backup file
            with open(db_backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # Process the data in a transaction
            with transaction.atomic():
                # First, delete all existing data in reverse order of dependencies
                from django.apps import apps
                from django.db import connection

                # Get all models in reverse order of dependencies
                models = list(apps.get_models())
                models.sort(key=lambda x: len(x._meta.fields), reverse=True)

                # Delete all data
                for model in models:
                    if model._meta.app_label not in ['contenttypes', 'auth']:
                        model.objects.all().delete()

                # Reset sequences
                with connection.cursor() as cursor:
                    for model in models:
                        if model._meta.app_label not in ['contenttypes', 'auth']:
                            table = model._meta.db_table
                            cursor.execute(
                                f"DELETE FROM sqlite_sequence WHERE name='{table}'")

                # Load new data
                for obj in serializers.deserialize('json', json.dumps(backup_data, ensure_ascii=False)):
                    try:
                        obj.save()
                    except Exception as e:
                        messages.warning(
                            request, f'Advertencia al restaurar {obj.object.__class__.__name__}: {str(e)}')

            # Restore media files
            media_backup_path = backup.get_media_backup_path()
            if os.path.exists(media_backup_path):
                if os.path.exists(settings.MEDIA_ROOT):
                    shutil.rmtree(settings.MEDIA_ROOT)
                shutil.copytree(media_backup_path, settings.MEDIA_ROOT)

            messages.success(request, 'Respaldo restaurado exitosamente')
        except Exception as e:
            # If restoration fails, restore from temporary backup
            try:
                # Convert temporary backup to UTF-8 as well
                with open(temp_backup_path, 'rb') as file:
                    raw_data = file.read()
                    detected = chardet.detect(raw_data)
                    encoding = detected['encoding']

                with codecs.open(temp_backup_path, 'r', encoding=encoding, errors='replace') as file:
                    content = file.read()

                with codecs.open(temp_backup_path, 'w', encoding='utf-8') as file:
                    file.write(content)

                with open(temp_backup_path, 'r', encoding='utf-8') as f:
                    temp_data = json.load(f)

                with transaction.atomic():
                    # First, delete all existing data in reverse order of dependencies
                    from django.apps import apps
                    from django.db import connection

                    # Get all models in reverse order of dependencies
                    models = list(apps.get_models())
                    models.sort(key=lambda x: len(
                        x._meta.fields), reverse=True)

                    # Delete all data
                    for model in models:
                        if model._meta.app_label not in ['contenttypes', 'auth']:
                            model.objects.all().delete()

                    # Reset sequences
                    with connection.cursor() as cursor:
                        for model in models:
                            if model._meta.app_label not in ['contenttypes', 'auth']:
                                table = model._meta.db_table
                                cursor.execute(
                                    f"DELETE FROM sqlite_sequence WHERE name='{table}'")

                    # Load backup data
                    for obj in serializers.deserialize('json', json.dumps(temp_data, ensure_ascii=False)):
                        try:
                            obj.save()
                        except Exception as e:
                            messages.warning(
                                request, f'Advertencia al restaurar {obj.object.__class__.__name__}: {str(e)}')

                messages.error(
                    request, f'Error al restaurar el respaldo: {str(e)}')
            except Exception as restore_error:
                messages.error(
                    request, f'Error crítico: No se pudo restaurar el respaldo ni recuperar el estado anterior. Error: {str(restore_error)}')
        finally:
            # Clean up temporary backup
            if os.path.exists(temp_backup_path):
                os.remove(temp_backup_path)

    except Exception as e:
        messages.error(request, f'Error al restaurar el respaldo: {str(e)}')

    return redirect('system_backup:backup_list')


@login_required
@user_passes_test(is_superuser)
def delete_backup(request, backup_id):
    """Delete a backup"""
    try:
        backup = get_object_or_404(Backup, id=backup_id)
        backup_path = backup.get_backup_path()

        if not os.path.exists(backup_path):
            messages.error(request, 'Respaldo no encontrado')
            return redirect('system_backup:backup_list')

        # Delete backup directory
        shutil.rmtree(backup_path)

        # Delete zip file if exists
        zip_path = backup.get_zip_path()
        if os.path.exists(zip_path):
            os.remove(zip_path)

        # Delete backup record
        backup.delete()

        messages.success(request, 'Respaldo eliminado exitosamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar el respaldo: {str(e)}')

    return redirect('system_backup:backup_list')


def get_dir_size(path):
    """Get directory size in human readable format"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)

    # Convert to human readable format
    for unit in ['B', 'KB', 'MB', 'GB']:
        if total_size < 1024:
            return f'{total_size:.1f} {unit}'
        total_size /= 1024
    return f'{total_size:.1f} TB'
