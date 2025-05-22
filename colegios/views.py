from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import Colegio
from .forms import ColegioForm

# Create your views here.


class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(
            self.request, 'No tienes permiso para acceder a esta página.')
        return redirect('dashboard:index')


class ColegioListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Colegio
    template_name = 'colegios/colegio_list.html'
    context_object_name = 'object_list'
    ordering = ['nombre']


class ColegioDetailView(LoginRequiredMixin, SuperuserRequiredMixin, DetailView):
    model = Colegio
    template_name = 'colegios/colegio_detail.html'
    context_object_name = 'colegio'
    slug_url_kwarg = 'slug'


class ColegioCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Colegio
    form_class = ColegioForm
    template_name = 'colegios/colegio_form.html'
    success_url = reverse_lazy('colegios:list')


class ColegioUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Colegio
    form_class = ColegioForm
    template_name = 'colegios/colegio_form.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('colegios:list')


class ColegioDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = Colegio
    template_name = 'colegios/colegio_confirm_delete.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('colegios:list')
