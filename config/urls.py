from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path("ping/", health_check),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),  # API URLs
    path('', include('public.urls')),
    path('dashboard', include('dashboard.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('colegios/', include('colegios.urls')),
    path('cursos/', include('cursos.urls')),
    path('estudiantes/', include('estudiantes.urls')),
    path('inventario/', include('inventario.urls')),
    path('salidas/', include('salidas.urls')),
    path('atrasos/', include('atrasos.urls')),
    path('reportes/', include('reportes.urls')),
    path('backup/', include('system_backup.urls')),  # URLs de respaldo
    path('salidas-almuerzo/', include('salidas_almuerzo.urls',
         namespace='salidas_almuerzo')),

    # URLs de autenticación
    path('accounts/login/',
         auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('accounts/logout/',
         auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(
        template_name='auth/password_change.html',
        success_url='/accounts/password_change/done/'
    ), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='auth/password_change_done.html'
    ), name='password_change_done'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html',
        email_template_name='auth/password_reset_email.html',
        subject_template_name='auth/password_reset_subject.txt'
    ), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    #
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
