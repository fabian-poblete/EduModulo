from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from .serializers import (
    UserSerializer, UserDetailSerializer, GroupSerializer,
    EstudianteSerializer, SalidaSerializer, AtrasoSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from estudiantes.models import Estudiante
from salidas.models import Salida
from atrasos.models import Atraso
from notificaciones.utils import enviar_notificacion

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_superuser(self, request):
        if not request.user.is_superuser:
            return Response(
                {"detail": "No tienes permisos para realizar esta acción."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data.get('password'))
            user.is_superuser = True
            user.is_staff = True
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data['username'])
            serializer = UserSerializer(user)
            response.data['user'] = serializer.data
            # Agregar información del colegio al token
            if hasattr(user, 'perfil') and user.perfil.colegio:
                response.data['colegio_id'] = user.perfil.colegio.id
                response.data['colegio_nombre'] = user.perfil.colegio.nombre
        return response


class EstudianteFilter(django_filters.FilterSet):
    """Filtro personalizado para estudiantes que permite búsqueda por RUT con conversión k↔0"""
    rut = django_filters.CharFilter(method='filter_rut')
    curso = django_filters.NumberFilter()
    activo = django_filters.BooleanFilter()

    def filter_rut(self, queryset, name, value):
        if value:
            # Limpiar el RUT de puntos, espacios y guiones
            rut_limpio = value.replace('.', '').replace(
                '-', '').replace(' ', '').upper()

            # Si termina en 'K', buscar tanto por 'K' como por '0' (insensible a mayúsculas)
            if rut_limpio.endswith('K'):
                rut_con_0 = rut_limpio[:-1] + '0'
                # Buscar insensible a mayúsculas/minúsculas
                return queryset.filter(
                    rut__iregex=r'^(' + rut_limpio[:-1] + '[Kk0])$'
                )

            # Si termina en '0', buscar tanto por '0' como por 'K' (insensible a mayúsculas)
            elif rut_limpio.endswith('0'):
                rut_con_k = rut_limpio[:-1] + 'K'
                # Buscar insensible a mayúsculas/minúsculas
                return queryset.filter(
                    rut__iregex=r'^(' + rut_limpio[:-1] + '[0Kk])$'
                )

            # Si no termina en 'K' ni '0', buscar exacto pero insensible a mayúsculas
            else:
                return queryset.filter(rut__iexact=rut_limpio)

        return queryset

    class Meta:
        model = Estudiante
        fields = ['curso', 'activo']


class EstudianteViewSet(viewsets.ModelViewSet):
    serializer_class = EstudianteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]

    filterset_class = EstudianteFilter  # Usar filtro personalizado
    search_fields = ['nombre', 'rut', 'email_estudiante',
                     'email_apoderado1', 'email_apoderado2']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']

    def get_queryset(self):
        queryset = Estudiante.objects.all()
        # Si el usuario no es del equipo de soporte, filtrar por su colegio
        if not self.request.user.perfil.es_equipo_soporte:
            queryset = queryset.filter(
                curso__colegio=self.request.user.perfil.colegio)
        return queryset

    @action(detail=True, methods=['get'])
    def salidas(self, request, pk=None):
        estudiante = self.get_object()
        salidas = Salida.objects.filter(estudiante=estudiante)
        serializer = SalidaSerializer(salidas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def atrasos(self, request, pk=None):
        estudiante = self.get_object()
        atrasos = Atraso.objects.filter(estudiante=estudiante)
        serializer = AtrasoSerializer(atrasos, many=True)
        return Response(serializer.data)


class SalidaViewSet(viewsets.ModelViewSet):
    queryset = Salida.objects.all()
    serializer_class = SalidaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estudiante', 'justificado', 'fecha']
    search_fields = ['estudiante__nombre', 'observacion']
    ordering_fields = ['fecha', 'hora']
    ordering = ['-fecha', '-hora']

    @action(detail=False, methods=['post'])
    def registrar_salida(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AtrasoViewSet(viewsets.ModelViewSet):
    queryset = Atraso.objects.all()
    serializer_class = AtrasoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estudiante',
                        'justificado', 'con_certificado', 'fecha']
    search_fields = ['estudiante__nombre', 'observacion']
    ordering_fields = ['fecha', 'hora']
    ordering = ['-fecha', '-hora']

    @action(detail=False, methods=['post'])
    def registrar_atraso(self, request):
        print("="*50)
        print("🚀 REGISTRO DE ATRASO INICIADO")
        print("="*50)

        serializer = self.get_serializer(data=request.data)
        print("📋 Serializer creado")

        if serializer.is_valid():
            print("✅ Serializer válido")
            print(f"📝 Datos validados: {serializer.validated_data}")

            atraso = serializer.save()
            print(f"💾 Atraso guardado: ID={atraso.id}")
            print(f"👨‍🎓 Estudiante: {atraso.estudiante.nombre}")
            print(f"🏫 Colegio: {atraso.estudiante.curso.colegio.nombre}")

            print("📱 ANTES de enviar_notificacion")
            try:
                enviar_notificacion(
                    evento=atraso,
                    estudiante=atraso.estudiante,
                    colegio=atraso.estudiante.curso.colegio,
                    tipo_evento='atraso'
                )
                print("✅ DESPUÉS de enviar_notificacion - FUNCIÓN COMPLETADA")
            except Exception as e:
                print(f"❌ ERROR en enviar_notificacion: {e}")
                import traceback
                traceback.print_exc()

            print("🔄 Retornando respuesta exitosa")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(f"❌ Serializer inválido: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
