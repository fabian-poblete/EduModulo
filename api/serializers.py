from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from estudiantes.models import Estudiante
from salidas.models import Salida
from atrasos.models import Atraso
from cursos.models import Curso

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


class CursoSerializer(serializers.ModelSerializer):
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
    estudiante = EstudianteSerializer(read_only=True)
    estudiante_id = serializers.PrimaryKeyRelatedField(
        queryset=Estudiante.objects.all(),
        write_only=True,
        source='estudiante'
    )

    class Meta:
        model = Salida
        fields = (
            'id', 'estudiante', 'estudiante_id', 'fecha', 'hora',
            'justificado', 'observacion', 'fecha_creacion', 'fecha_actualizacion'
        )
        read_only_fields = (
            'fecha', 'hora', 'fecha_creacion', 'fecha_actualizacion')


class AtrasoSerializer(serializers.ModelSerializer):
    estudiante = EstudianteSerializer(read_only=True)
    estudiante_id = serializers.PrimaryKeyRelatedField(
        queryset=Estudiante.objects.all(),
        write_only=True,
        source='estudiante'
    )

    class Meta:
        model = Atraso
        fields = (
            'id', 'estudiante', 'estudiante_id', 'fecha', 'hora',
            'justificado', 'observacion', 'fecha_creacion', 'fecha_actualizacion'
        )
        read_only_fields = (
            'fecha', 'hora', 'fecha_creacion', 'fecha_actualizacion')
