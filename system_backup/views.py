from django.shortcuts import render
import os
import json
import shutil
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import FileResponse, HttpResponseForbidden
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


def is_admin_colegio(user):
    return hasattr(user, 'perfil') and user.perfil.tipo_usuario == 'admin_colegio'


def get_colegio_for_admin(user):
    """Obtiene el colegio asociado a un usuario admin"""
    try:
        return user.perfil.colegio
    except:
        return None


@login_required
def backup_list(request):
    """List all backups"""
    if not request.user.is_superuser and not is_admin_colegio(request.user):
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    backups = Backup.objects.all()
    if not request.user.is_superuser:
        # Si es admin de colegio, solo mostrar sus respaldos
        colegio = get_colegio_for_admin(request.user)
        if colegio:
            backups = backups.filter(colegio=colegio)

    context = {
        'backups': backups,
        'is_admin_colegio': is_admin_colegio(request.user)
    }
    return render(request, 'system_backup/backup_list.html', context)


@login_required
def create_backup(request):
    """Create a new backup"""
    try:
        # Verificar permisos
        if not (request.user.is_superuser or is_admin_colegio(request.user)):
            return HttpResponseForbidden("No tienes permiso para crear respaldos")

        # Determinar el colegio
        colegio = None
        if is_admin_colegio(request.user):
            colegio = request.user.perfil.colegio

        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        if colegio:
            backup_dir = os.path.join(backup_dir, f'colegio_{colegio.id}')
            os.makedirs(backup_dir, exist_ok=True)

        # Generate timestamp for backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Use provided name if available, otherwise use timestamp
        backup_name = request.POST.get('backup_name', '').strip()
        if not backup_name:
            backup_name = f'backup_{timestamp}'
        backup_path = os.path.join(backup_dir, backup_name)

        # Create backup directory
        os.makedirs(backup_path, exist_ok=True)

        # Backup database with explicit encoding
        db_backup_path = os.path.join(backup_path, 'db_backup.json')
        try:
            # Construir el comando de dumpdata con filtros por colegio
            if colegio:
                # Crear un archivo temporal para cada modelo
                temp_files = []
                try:
                    # Primero el colegio
                    colegio_file = f'temp_colegio.json'
                    temp_files.append(colegio_file)
                    subprocess.run(
                        f'python manage.py dumpdata colegios.colegio --pks {colegio.id} --indent 2 -o {colegio_file}',
                        shell=True,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        encoding='utf-8'
                    )

                    # Luego los perfiles del colegio
                    perfiles_file = f'temp_perfiles.json'
                    temp_files.append(perfiles_file)
                    subprocess.run(
                        f'python manage.py dumpdata usuarios.perfil --indent 2 -o {perfiles_file}',
                        shell=True,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        encoding='utf-8'
                    )

                    # Combinar los archivos en el archivo final
                    all_data = []

                    # Leer y filtrar perfiles
                    with open(perfiles_file, 'r', encoding='utf-8') as f:
                        perfiles_data = json.load(f)
                        filtered_perfiles = [p for p in perfiles_data if p.get(
                            'fields', {}).get('colegio') == colegio.id]
                        all_data.extend(filtered_perfiles)

                    # Leer datos del colegio
                    with open(colegio_file, 'r', encoding='utf-8') as f:
                        colegio_data = json.load(f)
                        all_data.extend(colegio_data)

                    # Agregar otros modelos que necesitan filtrado por colegio
                    models_to_filter = [
                        'salidas.salida',
                        'atrasos.atraso',
                        'estudiantes.estudiante',
                        'cursos.curso',
                        'inventario.categoria'
                    ]

                    # Verificar modelos disponibles
                    from django.apps import apps
                    available_models = []
                    for model in models_to_filter:
                        try:
                            app_label, model_name = model.split('.')
                            Model = apps.get_model(app_label, model_name)
                            if Model is not None:
                                available_models.append(model)
                                print(
                                    f"Modelo {model} encontrado y disponible para respaldo")
                            else:
                                print(f"Modelo {model} no encontrado")
                        except LookupError as e:
                            print(f"Error al buscar modelo {model}: {str(e)}")

                    print(
                        f"\nIniciando respaldo de {len(available_models)} modelos disponibles...")

                    for model in available_models:
                        temp_file = f'temp_{model.replace(".", "_")}.json'
                        temp_files.append(temp_file)
                        try:
                            # Configuración específica para modelos problemáticos
                            if model == 'cursos.curso':
                                # Para cursos.curso, usar configuración especial con codificación latin1
                                dump_command = f'python manage.py dumpdata {model} --natural-foreign --natural-primary -o {temp_file}'
                                encoding = 'latin1'  # Forzar latin1 para cursos.curso
                            else:
                                dump_command = f'python manage.py dumpdata {model} --indent 2 -o {temp_file}'
                                encoding = 'utf-8'  # Usar utf-8 para otros modelos

                            # Ejecutar dumpdata
                            result = subprocess.run(
                                dump_command,
                                shell=True,
                                capture_output=True,
                                text=True,
                                encoding=encoding
                            )

                            if result.returncode == 0:
                                try:
                                    # Leer el archivo con la codificación específica
                                    with open(temp_file, 'r', encoding=encoding) as f:
                                        data = json.load(f)
                                        print(
                                            f"Archivo {model} leído exitosamente con codificación {encoding}")

                                    filtered_data = [item for item in data if item.get(
                                        'fields', {}).get('colegio') == colegio.id]
                                    print(
                                        f"Filtrados {len(filtered_data)} registros de {model} para el colegio {colegio.id}")
                                    all_data.extend(filtered_data)

                                except Exception as e:
                                    print(
                                        f"Error al procesar datos de {model}: {str(e)}")
                                    # Intentar método alternativo para cursos.curso
                                    if model == 'cursos.curso':
                                        print(
                                            f"Intentando método alternativo para {model}")
                                        try:
                                            Model = apps.get_model(
                                                *model.split('.'))
                                            data = []
                                            for obj in Model.objects.filter(colegio=colegio):
                                                data.append({
                                                    'model': model,
                                                    'pk': obj.pk,
                                                    'fields': {
                                                        'colegio': obj.colegio.id,
                                                        **{f.name: getattr(obj, f.name) for f in obj._meta.fields if f.name != 'colegio'}
                                                    }
                                                })
                                            print(
                                                f"Obtenidos {len(data)} registros de {model} usando ORM")
                                            all_data.extend(data)
                                        except Exception as e:
                                            print(
                                                f"Error en método alternativo para {model}: {str(e)}")
                            else:
                                print(
                                    f"Error al ejecutar dumpdata para {model}: {result.stderr}")

                        except Exception as e:
                            print(f"Error al procesar {model}: {str(e)}")

                    # Guardar todos los datos en el archivo final
                    with open(db_backup_path, 'w', encoding='utf-8') as f:
                        json.dump(all_data, f, indent=2, ensure_ascii=False)
                    print(
                        f"\nRespaldo completado con {len(all_data)} registros en total")

                finally:
                    # Limpiar archivos temporales
                    for temp_file in temp_files:
                        if os.path.exists(temp_file):
                            try:
                                os.remove(temp_file)
                            except Exception as e:
                                print(
                                    f"Error al eliminar archivo temporal {temp_file}: {str(e)}")
            else:
                # Para respaldos del sistema completo
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
        if colegio:
            # Solo respaldar archivos del colegio
            colegio_media_path = os.path.join(
                settings.MEDIA_ROOT, f'colegio_{colegio.id}')
            if os.path.exists(colegio_media_path):
                shutil.copytree(colegio_media_path, media_backup_path)
        elif os.path.exists(settings.MEDIA_ROOT):
            shutil.copytree(settings.MEDIA_ROOT, media_backup_path)

        # Create backup info file
        backup_info = {
            'timestamp': timestamp,
            'database': 'db_backup.json',
            'media': 'media' if os.path.exists(media_backup_path) else None,
            'colegio_id': colegio.id if colegio else None
        }

        with open(os.path.join(backup_path, 'backup_info.json'), 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)

        # Create backup record in database
        backup = Backup.objects.create(
            name=backup_name,
            size=get_dir_size(backup_path),
            status='success',
            description='Respaldo automático del sistema',
            colegio=colegio,
            created_by=request.user
        )

        messages.success(request, 'Respaldo creado exitosamente')
    except Exception as e:
        messages.error(request, f'Error al crear el respaldo: {str(e)}')

    return redirect('system_backup:backup_list')


@login_required
def download_backup(request, backup_id):
    """Download a backup file"""
    try:
        backup = get_object_or_404(Backup, id=backup_id)

        # Verificar permisos
        if not (request.user.is_superuser or
                (is_admin_colegio(request.user) and backup.colegio == request.user.perfil.colegio)):
            return HttpResponseForbidden("No tienes permiso para descargar este respaldo")

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
def restore_backup(request, backup_id):
    """Restore a backup"""
    try:
        backup = get_object_or_404(Backup, id=backup_id)

        # Verificar permisos
        if not (request.user.is_superuser or
                (is_admin_colegio(request.user) and backup.colegio == request.user.perfil.colegio)):
            return HttpResponseForbidden("No tienes permiso para restaurar este respaldo")

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
            # --- Manual temporary backup creation with ORM for school backups ---
            if backup.colegio:
                all_data = []
                colegio_id = backup.colegio.id

                # List of models to include in school temporary backup (should match create_backup)
                models_to_include = [
                    'colegios.colegio',
                    'usuarios.perfil',
                    'salidas.salida',
                    'atrasos.atraso',
                    'estudiantes.estudiante',
                    'cursos.curso',
                    'inventario.categoria',
                    # Add other models if they have a 'colegio' field and should be backed up per school
                ]

                from django.apps import apps

                for model_name in models_to_include:
                    try:
                        app_label, model = model_name.split('.')
                        Model = apps.get_model(app_label, model)
                        if hasattr(Model, 'colegio'):
                            queryset = Model.objects.filter(colegio=colegio_id)
                            # Manually serialize the queryset
                            for obj in queryset:
                                fields = {}
                                for field in obj._meta.fields:
                                    if field.name != 'colegio':  # Exclude colegio field from inner dict
                                        value = getattr(obj, field.name)
                                        # Handle potential non-json serializable values
                                        if isinstance(value, datetime):
                                            fields[field.name] = value.isoformat()
                                        else:
                                            try:
                                                # Attempt to JSON serialize, skip if fails
                                                json.dumps(value)
                                                fields[field.name] = value
                                            except (TypeError, OverflowError):
                                                # Fallback to string representation
                                                fields[field.name] = str(value)

                                all_data.append({
                                    'model': model_name,
                                    'pk': obj.pk,
                                    'fields': {'colegio': colegio_id, **fields}
                                })
                            print(
                                f"Temporalmente respaldados {queryset.count()} registros de {model_name} para el colegio {colegio_id}")
                        elif model_name == 'colegios.colegio':
                            queryset = Model.objects.filter(id=colegio_id)
                            for obj in queryset:
                                fields = {}
                                for field in obj._meta.fields:
                                    value = getattr(obj, field.name)
                                    if isinstance(value, datetime):
                                        fields[field.name] = value.isoformat()
                                    else:
                                        try:
                                            json.dumps(value)
                                            fields[field.name] = value
                                        except (TypeError, OverflowError):
                                            fields[field.name] = str(value)

                                all_data.append({
                                    'model': model_name,
                                    'pk': obj.pk,
                                    'fields': fields
                                })
                            print(
                                f"Temporalmente respaldado {queryset.count()} registro de {model_name} para el colegio {colegio_id}")

                        else:
                            print(
                                f"Saltando modelo {model_name} en respaldo temporal de colegio: no tiene campo 'colegio' y no es el modelo Colegio.")

                    except LookupError:
                        print(
                            f"Saltando modelo {model_name} en respaldo temporal de colegio: modelo no encontrado.")
                    except Exception as e:
                        print(
                            f"Error al procesar modelo {model_name} para respaldo temporal de colegio: {str(e)}")

                with open(temp_backup_path, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, indent=2, ensure_ascii=False)

            else:
                # For full system backups, use dumpdata without filter
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
            with open(db_backup_path, 'rb') as file:
                raw_data = file.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding']

            with codecs.open(db_backup_path, 'r', encoding=encoding, errors='replace') as file:
                content = file.read()

            with codecs.open(db_backup_path, 'w', encoding='utf-8') as file:
                file.write(content)

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

                # Delete all data for the specific colegio
                for model in models:
                    # Exclude the Backup model from deletion
                    if model == Backup:
                        print(f"Saltando eliminación de datos para el modelo Backup.")
                        continue

                    if model._meta.app_label not in ['contenttypes', 'auth']:
                        if backup.colegio:
                            # Si es un respaldo de colegio, solo eliminar datos de ese colegio
                            if hasattr(model, 'colegio'):
                                model.objects.filter(
                                    colegio=backup.colegio).delete()
                        else:
                            # Si es un respaldo del sistema, eliminar todos los datos
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
                if backup.colegio:
                    # Restaurar solo los archivos del colegio
                    colegio_media_path = os.path.join(
                        settings.MEDIA_ROOT, f'colegio_{backup.colegio.id}')
                    if os.path.exists(colegio_media_path):
                        shutil.rmtree(colegio_media_path)
                    shutil.copytree(media_backup_path, colegio_media_path)
                else:
                    # Restaurar todos los archivos
                    if os.path.exists(settings.MEDIA_ROOT):
                        shutil.rmtree(settings.MEDIA_ROOT)
                    shutil.copytree(media_backup_path, settings.MEDIA_ROOT)

            messages.success(request, 'Respaldo restaurado exitosamente')

        except Exception as e:
            # If main restoration fails, try to restore from temporary backup
            messages.error(
                request, f'Error al restaurar el respaldo: {str(e)}')
            try:
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

                    # Delete all data for the specific colegio
                    for model in models:
                        # Exclude the Backup model from deletion
                        if model == Backup:
                            print(
                                f"Saltando eliminación de datos para el modelo Backup.")
                            continue

                        if model._meta.app_label not in ['contenttypes', 'auth']:
                            if backup.colegio:
                                if hasattr(model, 'colegio'):
                                    model.objects.filter(
                                        colegio=backup.colegio).delete()
                            else:
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
                    # Use 'e' from the inner except
                    request, f'Error crítico: No se pudo restaurar el respaldo ni recuperar el estado anterior. Error: {str(e)}')
            finally:
                # Clean up temporary backup
                if os.path.exists(temp_backup_path):
                    os.remove(temp_backup_path)

    except Exception as e:
        # This outer except catches exceptions from the initial temporary backup creation or any unexpected errors outside the main try/except block
        messages.error(
            request, f'Error general durante la restauración: {str(e)}')

    return redirect('system_backup:backup_list')


@login_required
def delete_backup(request, backup_id):
    """Delete a backup"""
    try:
        backup = get_object_or_404(Backup, id=backup_id)

        # Verificar permisos
        if not (request.user.is_superuser or
                (is_admin_colegio(request.user) and backup.colegio == request.user.perfil.colegio)):
            return HttpResponseForbidden("No tienes permiso para eliminar este respaldo")

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
