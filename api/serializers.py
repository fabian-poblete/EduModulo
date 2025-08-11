from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from estudiantes.models import Estudiante
from salidas.models import Salida
from atrasos.models import Atraso
from cursos.models import Curso, Colegio

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'is_active', 'is_staff')
        read_only_fields = ('id',)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class UserDetailSerializer(UserSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('groups',)


class ColegioSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colegio
        fields = ('id', 'nombre')


class CursoSerializer(serializers.ModelSerializer):
    colegio = ColegioSimpleSerializer(read_only=True)

    class Meta:
        model = Curso
        fields = ('id', 'nombre', 'colegio')


class EstudianteSerializer(serializers.ModelSerializer):
    curso = CursoSerializer(read_only=True)
    curso_id = serializers.PrimaryKeyRelatedField(
        queryset=Curso.objects.all(),
        write_only=True,
        source='curso'
    )
    rut_formateado = serializers.SerializerMethodField()

    class Meta:
        model = Estudiante
        fields = (
            'id', 'nombre', 'rut', 'rut_formateado', 'curso', 'curso_id',
            'email_estudiante', 'email_apoderado1', 'email_apoderado2',
            'telefono_apoderado1', 'telefono_apoderado2', 'activo',
            'fecha_creacion', 'fecha_actualizacion'
        )
        read_only_fields = ('fecha_creacion', 'fecha_actualizacion')

    def get_rut_formateado(self, obj):
        return obj.formatear_rut()


class SalidaSerializer(serializers.ModelSerializer):
    estudiante = serializers.SlugRelatedField(
        queryset=Estudiante.objects.all(),
        slug_field='rut',
        write_only=True
    )

    class Meta:
        model = Salida
        fields = ('id', 'estudiante', 'fecha', 'hora',
                  'justificado', 'observacion')
        read_only_fields = ('fecha', 'hora')


class AtrasoSerializer(serializers.ModelSerializer):
    # Cambiar a CharField para validación personalizada
    estudiante = serializers.CharField(write_only=True)

    def validate_estudiante(self, value):
        """Validar y convertir el RUT del estudiante con lógica k↔0"""
        if not value:
            raise serializers.ValidationError(
                "El RUT del estudiante es requerido")

        # Limpiar el RUT de puntos, espacios y guiones
        rut_limpio = value.replace('.', '').replace(
            '-', '').replace(' ', '').upper()

        # Si termina en 'K', buscar por 'K' y por '0'
        if rut_limpio.endswith('K'):
            rut_con_0 = rut_limpio[:-1] + '0'
            estudiante = Estudiante.objects.filter(
                rut__in=[rut_limpio, rut_con_0]).first()
        # Si termina en '0', buscar por '0' y por 'K'
        elif rut_limpio.endswith('0'):
            rut_con_k = rut_limpio[:-1] + 'K'
            estudiante = Estudiante.objects.filter(
                rut__in=[rut_limpio, rut_con_k]).first()
        # Si no termina en 'K' ni '0', buscar exacto
        else:
            estudiante = Estudiante.objects.filter(rut=rut_limpio).first()

        if not estudiante:
            raise serializers.ValidationError(
                f"Estudiante con RUT {value} no encontrado")

        # Retornar el ID del estudiante para la inserción
        return estudiante.id

    class Meta:
        model = Atraso
        fields = ('id', 'estudiante', 'fecha', 'hora',
                  'justificado', 'observacion')
        read_only_fields = ('fecha', 'hora')
