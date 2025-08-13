#!/usr/bin/env python3
"""
Script para probar el filtro de RUT corregido
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from estudiantes.models import Estudiante
from api.views import EstudianteFilter

def test_filtro_rut():
    """Probar el filtro de RUT corregido"""
    print("🧪 PROBANDO FILTRO DE RUT CORREGIDO")
    print("=" * 60)
    
    # Crear instancia del filtro
    filtro = EstudianteFilter()
    
    # Caso 1: RUT con "K" mayúscula (como lo envía la app de escritorio)
    print("=== CASO 1: RUT con 'K' mayúscula ===")
    rut_buscar = "22784096K"
    print(f"Buscando: {rut_buscar}")
    
    # Aplicar filtro
    queryset = Estudiante.objects.all()
    queryset_filtrado = filtro.filter_rut(queryset, 'rut', rut_buscar)
    
    if queryset_filtrado.exists():
        print(f"✅ Encontrados {queryset_filtrado.count()} estudiantes:")
        for est in queryset_filtrado:
            print(f"  - {est.nombre}: {est.rut}")
    else:
        print("❌ No se encontraron estudiantes")
    
    print()
    
    # Caso 2: RUT con "0" al final (como lo ingresa el usuario)
    print("=== CASO 2: RUT con '0' al final ===")
    rut_buscar = "227840960"
    print(f"Buscando: {rut_buscar}")
    
    # Aplicar filtro
    queryset = Estudiante.objects.all()
    queryset_filtrado = filtro.filter_rut(queryset, 'rut', rut_buscar)
    
    if queryset_filtrado.exists():
        print(f"✅ Encontrados {queryset_filtrado.count()} estudiantes:")
        for est in queryset_filtrado:
            print(f"  - {est.nombre}: {est.rut}")
    else:
        print("❌ No se encontraron estudiantes")
    
    print()
    
    # Caso 3: RUT con "k" minúscula (como está en la BD)
    print("=== CASO 3: RUT con 'k' minúscula ===")
    rut_buscar = "22784096k"
    print(f"Buscando: {rut_buscar}")
    
    # Aplicar filtro
    queryset = Estudiante.objects.all()
    queryset_filtrado = filtro.filter_rut(queryset, 'rut', rut_buscar)
    
    if queryset_filtrado.exists():
        print(f"✅ Encontrados {queryset_filtrado.count()} estudiantes:")
        for est in queryset_filtrado:
            print(f"  - {est.nombre}: {est.rut}")
    else:
        print("❌ No se encontraron estudiantes")
    
    print()
    
    # Caso 4: Verificar que el estudiante existe directamente
    print("=== CASO 4: Verificación directa en BD ===")
    estudiante_directo = Estudiante.objects.filter(rut__iexact="22784096K").first()
    
    if estudiante_directo:
        print(f"✅ Estudiante encontrado directamente:")
        print(f"  - Nombre: {estudiante_directo.nombre}")
        print(f"  - RUT: {estudiante_directo.rut}")
        print(f"  - Curso: {estudiante_directo.curso.nombre}")
    else:
        print("❌ No se encontró el estudiante directamente")
        
        # Buscar con regex insensible
        estudiante_regex = Estudiante.objects.filter(rut__iregex=r'^22784096[Kk0]$').first()
        if estudiante_regex:
            print(f"✅ Estudiante encontrado con regex:")
            print(f"  - Nombre: {estudiante_regex.nombre}")
            print(f"  - RUT: {estudiante_regex.rut}")
        else:
            print("❌ No se encontró con regex tampoco")

if __name__ == "__main__":
    test_filtro_rut()
