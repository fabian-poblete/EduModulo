from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from colegios.models import Colegio


class Command(BaseCommand):
    help = 'Carga datos de muestra para el módulo de inventario'

    def handle(self, *args, **kwargs):
        # Crear superusuario si no existe
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Superusuario creado'))

        # Crear colegio de muestra si no existe
        colegio, created = Colegio.objects.get_or_create(
            nombre='Colegio de Muestra',
            defaults={
                'direccion': 'Calle Principal #123',
                'telefono': '123-456-7890',
                'email': 'info@colegiodemuestra.com',
                'ciudad': 'Ciudad de Muestra'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Colegio de muestra creado'))

        # Cargar fixtures
        fixtures = [
            'categorias.json',
            'estados.json',
            'ubicaciones.json',
            'articulos.json'
        ]

        for fixture in fixtures:
            try:
                call_command('loaddata', f'inventario/fixtures/{fixture}')
                self.stdout.write(self.style.SUCCESS(
                    f'Fixture {fixture} cargado exitosamente'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error al cargar {fixture}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(
            'Datos de muestra cargados exitosamente'))
