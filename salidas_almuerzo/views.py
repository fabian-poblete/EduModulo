from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from .models import AutorizacionAlmuerzo, RegistroSalidaAlmuerzo
from estudiantes.models import Estudiante
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from django.views.generic.edit import DeleteView
from django.http import JsonResponse
from django.db.models import Q
from django import forms
import pandas as pd
import io
from django.http import HttpResponse
import numpy as np


class AutorizadosAlmuerzoListView(LoginRequiredMixin, ListView):
    model = AutorizacionAlmuerzo
    template_name = 'salidas_almuerzo/autorizados_list.html'
    context_object_name = 'autorizados'

    def get_queryset(self):
        return AutorizacionAlmuerzo.objects.filter(autorizado=True, fecha_fin__gte=timezone.now().date())


class AutorizarAlmuerzoCreateView(LoginRequiredMixin, CreateView):
    model = AutorizacionAlmuerzo
    fields = ['estudiante', 'fecha_inicio', 'fecha_fin', 'observaciones']
    template_name = 'salidas_almuerzo/autorizar_form.html'
    success_url = reverse_lazy('salidas_almuerzo:autorizados_list')

    def form_valid(self, form):
        if form.cleaned_data['fecha_fin'] and form.cleaned_data['fecha_inicio'] > form.cleaned_data['fecha_fin']:
            form.add_error(
                'fecha_fin', 'La fecha de fin no puede ser anterior a la fecha de inicio.')
            return self.form_invalid(form)
        form.instance.autorizado = True
        return super().form_valid(form)


class AutorizarAlmuerzoUpdateView(LoginRequiredMixin, UpdateView):
    model = AutorizacionAlmuerzo
    fields = ['fecha_inicio', 'fecha_fin', 'observaciones']
    template_name = 'salidas_almuerzo/autorizar_form.html'
    success_url = reverse_lazy('salidas_almuerzo:autorizados_list')

    def form_valid(self, form):
        if form.cleaned_data['fecha_fin'] and form.cleaned_data['fecha_inicio'] > form.cleaned_data['fecha_fin']:
            form.add_error(
                'fecha_fin', 'La fecha de fin no puede ser anterior a la fecha de inicio.')
            return self.form_invalid(form)
        # Forzar el estudiante original y autorizado=True
        form.instance.estudiante = self.get_object().estudiante
        form.instance.autorizado = True
        return super().form_valid(form)


class VerificarPermisoView(LoginRequiredMixin, View):
    template_name = 'salidas_almuerzo/verificar_permiso.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        rut = request.POST.get('rut')
        estudiante = Estudiante.objects.filter(rut=rut).first()
        autorizacion = None
        if estudiante:
            autorizacion = AutorizacionAlmuerzo.objects.filter(
                estudiante=estudiante, autorizado=True, fecha_fin__gte=timezone.now().date()).first()
        return render(request, self.template_name, {'estudiante': estudiante, 'autorizacion': autorizacion})


class RegistrarSalidaView(LoginRequiredMixin, View):
    template_name = 'salidas_almuerzo/registrar_salida.html'

    def post(self, request):
        estudiante_id = request.POST.get('estudiante_id')
        estudiante = get_object_or_404(Estudiante, id=estudiante_id)
        registro, created = RegistroSalidaAlmuerzo.objects.get_or_create(
            estudiante=estudiante,
            fecha=timezone.now().date(),
            defaults={'hora_salida': timezone.now().time(),
                      'autorizado_por': request.user}
        )
        if not created:
            messages.warning(
                request, 'Ya existe un registro de salida para hoy.')
        else:
            messages.success(request, 'Salida registrada correctamente.')
        return redirect('salidas_almuerzo:verificar_permiso')


class RegistrarRegresoView(LoginRequiredMixin, View):
    def post(self, request):
        estudiante_id = request.POST.get('estudiante_id')
        estudiante = get_object_or_404(Estudiante, id=estudiante_id)
        registro = RegistroSalidaAlmuerzo.objects.filter(
            estudiante=estudiante, fecha=timezone.now().date()).first()
        if registro and not registro.hora_regreso:
            registro.hora_regreso = timezone.now().time()
            registro.save()
            messages.success(request, 'Regreso registrado correctamente.')
        else:
            messages.warning(
                request, 'No se encontró registro de salida o ya se registró el regreso.')
        return redirect('salidas_almuerzo:verificar_permiso')


class DesautorizarAlmuerzoView(LoginRequiredMixin, View):
    def post(self, request, pk):
        autorizacion = get_object_or_404(AutorizacionAlmuerzo, pk=pk)
        autorizacion.autorizado = False
        autorizacion.save()
        messages.success(request, 'Estudiante desautorizado correctamente.')
        return redirect('salidas_almuerzo:autorizados_list')


class BuscarEstudiantesAlmuerzoView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '')
        if len(query) < 2:
            return JsonResponse([], safe=False)
        colegio = None
        if not request.user.is_superuser and hasattr(request.user, 'perfil'):
            colegio = request.user.perfil.colegio
        estudiantes = Estudiante.objects.filter(
            Q(nombre__icontains=query) | Q(rut__icontains=query),
            activo=True
        )
        if colegio:
            estudiantes = estudiantes.filter(curso__colegio=colegio)
        estudiantes = estudiantes[:20]
        results = []
        for estudiante in estudiantes:
            results.append({
                'id': estudiante.id,
                'nombre': estudiante.nombre,
                'rut': estudiante.rut,
                'curso': estudiante.curso.nombre
            })
        return JsonResponse(results, safe=False)


class CargaMasivaAutorizadosForm(forms.Form):
    archivo = forms.FileField(label='Archivo Excel (.xlsx)', required=True)


class CargaMasivaAutorizadosView(LoginRequiredMixin, View):
    template_name = 'salidas_almuerzo/carga_masiva.html'
    form_class = CargaMasivaAutorizadosForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        resultados = []
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            try:
                df = pd.read_excel(archivo)
                requeridos = {'rut', 'fecha_inicio', 'fecha_fin'}
                if not requeridos.issubset(df.columns.str.lower()):
                    messages.error(
                        request, 'El archivo debe contener las columnas: rut, fecha_inicio, fecha_fin.')
                    return render(request, self.template_name, {'form': form})
                for idx, row in df.iterrows():
                    rut = str(row.get('rut', '')).strip()
                    fecha_inicio = row.get('fecha_inicio')
                    fecha_fin = row.get('fecha_fin')
                    observaciones = row.get('observaciones', '')
                    if pd.isna(observaciones) or str(observaciones).strip().lower() == 'nan':
                        observaciones = ''
                    estudiante = Estudiante.objects.filter(
                        rut__iexact=rut).first()
                    if not estudiante:
                        resultados.append(
                            {'rut': rut, 'resultado': 'No encontrado'})
                        continue
                    autorizacion, created = AutorizacionAlmuerzo.objects.update_or_create(
                        estudiante=estudiante,
                        defaults={
                            'autorizado': True,
                            'fecha_inicio': fecha_inicio,
                            'fecha_fin': fecha_fin,
                            'observaciones': observaciones
                        }
                    )
                    resultados.append(
                        {'rut': rut, 'resultado': 'Autorizado' if created else 'Actualizado'})
                messages.success(
                    request, f"Procesados {len(resultados)} registros.")
            except Exception as e:
                messages.error(request, f'Error procesando el archivo: {e}')
        return render(request, self.template_name, {'form': form, 'resultados': resultados})


class DescargarEjemploExcelView(LoginRequiredMixin, View):
    def get(self, request):
        import pandas as pd
        from io import BytesIO
        data = [{
            'rut': '12345678K',
            'fecha_inicio': '2025-03-01',
            'fecha_fin': '2025-12-31',
            'observaciones': 'Ejemplo de autorización'
        }]
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        response = HttpResponse(output.read(
        ), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=ejemplo_carga_autorizados.xlsx'
        return response
