from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet, GroupViewSet, CustomTokenObtainPairView,
    EstudianteViewSet, SalidaViewSet, AtrasoViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'estudiantes', EstudianteViewSet,basename='estudiantes')
router.register(r'salidas', SalidaViewSet)
router.register(r'atrasos', AtrasoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
