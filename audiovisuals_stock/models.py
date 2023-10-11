from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from django.core.validators import MinValueValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El Email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=255)  # Puedes agregar campos personalizados aquí
    rol = models.CharField(max_length=255)

    # Agrega cualquier otro campo personalizado que necesites
    userprofile = models.OneToOneField('UserProfile', on_delete=models.CASCADE, related_name='custom_user')
    #userprofile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='profile', default=1)  # Puedes ajustar el valor predeterminado según tus necesidades

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    # Agrega cualquier otro campo requerido aquí si es necesario

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    nombre = models.TextField(blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.user.email

    def obtener_deudas_pendientes(self):
        return DeudaMaterial.objects.filter(usuario=self.user, devuelta=False)



#================ CREACION DE MATERIALES ================#

class TipoMaterial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre
    
    
class Material(models.Model):
    referencia = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField()
    tipo = models.ForeignKey(TipoMaterial, on_delete=models.CASCADE)
    creadopor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    fecha_compra = models.DateField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    numero_serie = models.CharField(max_length=100)

class DeudaMaterial(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad_adeudada = models.PositiveIntegerField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField()  # Define cómo calcular la fecha de vencimiento
    devuelta = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Calcula la fecha de vencimiento al momento de guardar la deuda
        if not self.fecha_vencimiento:
            self.fecha_vencimiento = timezone.now() + timezone.timedelta(days=7)  # Por ejemplo, 7 días desde la generación
        super(DeudaMaterial, self).save(*args, **kwargs)

class ExtraccionMaterial(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cantidad_extraida = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],  # Esto asegura que la cantidad sea mayor que cero
    )
    fecha_extraccion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Comprobar si la cantidad extraída es mayor que la cantidad disponible
        if self.cantidad_extraida > self.material.cantidad:
            raise ValidationError("La cantidad a extraer no puede ser mayor que la cantidad disponible.")
        
        super(ExtraccionMaterial, self).save(*args, **kwargs)
        
        # Crear automáticamente una deuda asociada a la extracción
        if not DeudaMaterial.objects.filter(usuario=self.usuario, material=self.material, devuelta=False).exists():
            DeudaMaterial.objects.create(
                usuario=self.usuario,
                material=self.material,
                cantidad_adeudada=self.cantidad_extraida,
            )

class DevolucionMaterial(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cantidad_devuelta = models.PositiveIntegerField()
    fecha_devolucion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Comprobar si la cantidad devuelta es menor o igual a la cantidad extraída
        if self.cantidad_devuelta > self.material.cantidad:
            raise ValidationError("La cantidad devuelta no puede ser mayor que la cantidad extraída.")
        
        super(DevolucionMaterial, self).save(*args, **kwargs)
        
        # Marcar la deuda asociada como devuelta
        deuda = DeudaMaterial.objects.filter(usuario=self.usuario, material=self.material, devuelta=False).first()
        if deuda:
            deuda.devuelta = True
            deuda.save()

#================ LOGS DE MATERIALES ================#
class MaterialLog(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cantidad_extraida = models.PositiveIntegerField()
    fecha_accion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.usuario} extrajo {self.cantidad_extraida} de {self.material.nombre}'
    

#================ REGISTRO DE ACTIVIDAD ================#
class UserActivity(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ACTION_CHOICES = (
        ('create', 'Crear'),
        ('update', 'Modificar'),
        ('delete', 'Borrar'),
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} - {self.action} - {self.material} - {self.timestamp}'