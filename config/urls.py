from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('public.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('colegios/', include('colegios.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('cursos/', include('cursos.urls')),
    path('estudiantes/', include('estudiantes.urls')),
    path('comunicaciones/', include('comunicaciones.urls', namespace='comunicaciones')),
    path('salidas/', include('salidas.urls', namespace='salidas')),
    path('revision_pruebas/', include('revision_pruebas.urls',
         namespace='revision_pruebas')),
    path('atrasos/', include('atrasos.urls', namespace='atrasos')),
    path('inventario/', include('inventario.urls', namespace='inventario')),
    

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

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
