from .models import UserProfile, CustomUser
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import IntegrityError
from .models import Material
from .models import Material, MaterialLog, Proveedor, TipoMaterial, DeudaMaterial
from .forms import UserProfileForm, CustomUserCreationForm, MaterialForm, MaterialEditForm, ExtraccionMaterialForm, TipoMaterialForm, ProveedorForm

# ================ VISTA DEL REGISTRO ================
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                # Intenta crear un perfil para el usuario si no tiene uno
                user.userprofile  # Esto generará una excepción si no existe un perfil
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user)
                
            login(request, user)
            return redirect('home')  # Redirige al usuario a la página de inicio después del registro exitoso
        else:
            # En caso de que el formulario no sea válido, renderiza el formulario con los errores
            return render(request, 'audiovisuals_stock/signup.html', {'form': form})
    else:
        form = CustomUserCreationForm()
    return render(request, 'audiovisuals_stock/signup.html', {'form': form})

# ================ VISTA DEL LOGIN ================
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')  # Utiliza la solicitud en lugar del usuario directamente
            return redirect('home')  # Redirige al usuario a la página de inicio después del inicio de sesión exitoso
        else:
            # En caso de que el formulario no sea válido, renderiza el formulario con los errores
            return render(request, 'audiovisuals_stock/login.html', {'form': form})
    else:
        form = AuthenticationForm()
    return render(request, 'audiovisuals_stock/login.html', {'form': form})


# ================ VISTA HOME ================
def home(request):
    if not request.user.is_authenticated:
        # Si el usuario no ha iniciado sesión, redirige a la página de inicio de sesión
        return redirect(reverse('login'))  # Ajusta 'login' al nombre de la URL de tu página de inicio de sesión
    else:
        # Renderiza el archivo HTML o crea el contenido HTML aquí
        return render(request, 'audiovisuals_stock/home.html')


# ================ VISTA DEL PERFIL ================
def view_profile(request):
    if request.user.is_authenticated:
        user = request.user

        if request.method == 'POST':
            deuda_id = request.POST.get('deuda_id')
            deuda = DeudaMaterial.objects.get(id=deuda_id)
            deuda.devuelta = True
            deuda.save()
            # Obtén el material asociado a esta deuda
            material = deuda.material
            # Suma la cantidad adeudada devuelta a la cantidad del material
            material.cantidad += deuda.cantidad_adeudada
            material.save()
            return redirect('view_profile')

        deudas_pendientes = DeudaMaterial.objects.filter(usuario=user, devuelta=False)

        context = {
            'user': user,
            'deudas_pendientes': deudas_pendientes
        }
        return render(request, 'audiovisuals_stock/perfil.html', context)
    else:
        return redirect(reverse('login'))
    

# ================ VISTA EDITAR PERFIL ================ #
def edit_profile(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = UserProfileForm(request.POST, instance=request.user.userprofile)
            if form.is_valid():
                form.save()
                return redirect(reverse('perfil'))
        else:
            form = UserProfileForm(instance=request.user.userprofile)
        return render(request, 'audiovisuals_stock/editar_perfil.html', {'form': form})
    else:
            # Usuario no autenticado, manejarlo según tus requerimientos
            return redirect(reverse('login'))
    

# ================  ================ #
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# ================ VISTA VER MATERIAL ================ #
def detalle_material(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    return render(request, 'audiovisuals_stock/detalle_material.html', {'material': material})

# ================ VISTA CREAR MATERIAL ================ #
def subir_material(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = MaterialForm(request.POST)
            if form.is_valid():
                # Guarda el material en la base de datos
                material = form.save(commit=False)
                # Establece el usuario creador del material
                material.creadopor = request.user
                material.save()
                # Redirige al usuario a la página de lista de materiales
                return redirect('list_material')
        else:
            form = MaterialForm()
        
        return render(request, 'audiovisuals_stock/crear_material.html', {'form': form})
    else:
        # Usuario no autenticado, manejarlo según tus requerimientos
        return redirect('login')  # Puedes usar 'login' en lugar de reverse('login') si has configurado correctamente las URLs en tu proyecto


# ================ VISTA LISTA MATERIALES ================ #
def lista_materiales(request):
    if request.user.is_authenticated:
        materiales = Material.objects.all()
        return render(request, 'audiovisuals_stock/list_material.html', {'materiales': materiales})
    else:
        # Usuario no autenticado, manejarlo según tus requerimientos
        return redirect(reverse('login'))


# ================ VISTA EDITAR MATERIAL ================ #
def editar_material(request, material_id):
    if request.user.is_authenticated:
        material = get_object_or_404(Material, pk=material_id)
        if request.method == 'POST':
            form = MaterialEditForm(request.POST, instance=material)
            if form.is_valid():
                form.save()
                return redirect('list_material')  # Puedes redirigir a donde desees después de editar
        else:
            form = MaterialEditForm(instance=material)

        return render(request, 'audiovisuals_stock/editar_material.html', {'form': form, 'material': material})
    else:
        # Usuario no autenticado, manejarlo según tus requerimientos
        return redirect(reverse('login'))

# ================ VISTA PARA EXTRAER MATERIAL ================ #
def extraer_material(request, material_id):
    # Obtener el material basado en su ID
    material = Material.objects.get(id=material_id)

    if request.method == 'POST':
        # Si la solicitud es un POST, procesar el formulario
        form = ExtraccionMaterialForm(request.POST)

        if form.is_valid():
            cantidad_extraida = form.cleaned_data['cantidad_extraida']

            # Verificar si la cantidad a extraer es menor o igual a la cantidad disponible
            if cantidad_extraida <= material.cantidad:
                try:
                    # Realizar la extracción y guardar el registro en el log
                    material.cantidad -= cantidad_extraida
                    material.save()

                    log = MaterialLog(material=material, usuario=request.user, cantidad_extraida=cantidad_extraida)
                    log.save()

                    # Verificar si ya existe una deuda para este usuario y material
                    deuda_existente = DeudaMaterial.objects.filter(usuario=request.user, material=material, devuelta=False).first()

                    # Si no existe una deuda, crear una nueva
                    if not deuda_existente:
                        deuda_existente = DeudaMaterial.objects.create(
                            usuario=request.user,
                            material=material,
                            cantidad_adeudada=cantidad_extraida,
                        )
                    else:
                        # Si la deuda existe, actualizar la cantidad adeudada
                        deuda_existente.cantidad_adeudada += cantidad_extraida
                        deuda_existente.save()

                    # Redirigir al perfil del usuario
                    return redirect('view_profile')
                except IntegrityError as e:
                    # Manejar errores de integridad (por ejemplo, si se produce una extracción duplicada)
                    form.add_error(None, 'Error de extracción: ' + str(e))
            else:
                # Mostrar error si la cantidad a extraer es mayor que la cantidad disponible
                form.add_error(None, 'La cantidad a extraer es mayor que la cantidad disponible')
    else:
        # Si la solicitud no es un POST, mostrar el formulario vacío
        form = ExtraccionMaterialForm()

    # Obtener las deudas pendientes del usuario
    deudas_pendientes = DeudaMaterial.objects.filter(usuario=request.user, devuelta=False)

    # Renderizar la plantilla con el formulario, el material y las deudas pendientes
    return render(request, 'audiovisuals_stock/extraer_material.html', {'form': form, 'material': material, 'deudas_pendientes': deudas_pendientes})


    
# ================ VISTA PARA DEVOLVER MATERIAL ================ #
def saldar_deuda(request, deuda_id):
    deuda = DeudaMaterial.objects.get(id=deuda_id)

    if request.method == 'POST':
        form = ExtraccionMaterialForm(request.POST)

        if form.is_valid():
            cantidad_devuelta = form.cleaned_data['cantidad_devuelta']

            if cantidad_devuelta <= 0:
                form.add_error(None, 'La cantidad a devolver debe ser mayor que cero')
            else:
                try:
                    deuda.devolver_cantidad(cantidad_devuelta, request.user)

                    # Redirigir nuevamente al perfil del usuario
                    return redirect('view_profile')
                except IntegrityError as e:
                    form.add_error(None, 'Error de devolución: La cantidad a devolver no es válida')
        else:
            form.add_error(None, 'Error en el formulario')

    # Redirigir nuevamente al perfil del usuario en caso de que no se haya saldado la deuda
    return redirect('view_profile')


# ================ VISTA PARA EL LOG DEL MATERIAL ================ #
def log_material(request, material_id):
    if request.user.is_authenticated:
        material = Material.objects.get(id=material_id)
        log = MaterialLog.objects.filter(material=material).order_by('-fecha_accion')
        return render(request, 'audiovisuals_stock/log_material.html', {'material': material, 'log': log})
    else:
        # Usuario no autenticado, manejarlo según tus requerimientos
        return redirect(reverse('login'))

# ================ AGREGAR TIPOS PARA MATERIAL ================ #
def agregar_tipo_material(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = TipoMaterialForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('agregar_tipo_material')  # Redirige a la página de lista de materiales u otra de tu elección
        else:
            form = TipoMaterialForm()
        
        # Obtén la lista de proveedores existentes
        tiposmaterial = TipoMaterial.objects.all()

        # Lógica para eliminar proveedores
        if 'eliminar_tipomaterial' in request.POST:
            tipomaterial_id = request.POST['eliminar_tipomaterial']
            tipomaterial = get_object_or_404(TipoMaterial, id=tipomaterial_id)
            tipomaterial.delete()
            return redirect('agregar_tipo_material')  # Redirige nuevamente a la misma vista después de eliminar
        
        return render(request, 'audiovisuals_stock/agregar_tipo_material.html', {'form': form, 'tiposmaterial':tiposmaterial})
    else:
        # Usuario no autenticado, manejarlo según tus requerimientos
        return redirect(reverse('login'))

# ================ AGREGAR PROVEEDOR ================ #
def agregar_proveedor(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = ProveedorForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('agregar_proveedor')  # Redirige a la página de lista de materiales u otra de tu elección
        else:
            form = ProveedorForm()

        # Obtén la lista de proveedores existentes
        proveedores = Proveedor.objects.all()

        # Lógica para eliminar proveedores
        if 'eliminar_proveedor' in request.POST:
            proveedor_id = request.POST['eliminar_proveedor']
            proveedor = get_object_or_404(Proveedor, id=proveedor_id)
            proveedor.delete()
            return redirect('agregar_proveedor')  # Redirige nuevamente a la misma vista después de eliminar
        
        return render(request, 'audiovisuals_stock/agregar_proveedor.html', {'form': form, 'proveedores': proveedores})
    else:
        # Usuario no autenticado, manejarlo según tus requerimientos
        return redirect(reverse('login'))
    

def obtener_deudas_pendientes(self):
    # Obtener todas las deudas pendientes del usuario actual
    deudas_pendientes = DeudaMaterial.objects.filter(usuario=self.user, devuelta=False)
    
    # Agregar declaraciones de depuración
    print(f'Deudas pendientes para el usuario {self.user.email}:')
    for deuda in deudas_pendientes:
        print(f'{deuda.material.nombre} - Cantidad: {deuda.cantidad_adeudada}')
    
    return deudas_pendientes

# ================  404 ================ #
def error_404(request, exception):
    return render(request, '404.html', status=404)

# ================  CALENDAR ================ #
def calendar(request):
    if not request.user.is_authenticated:
        # Si el usuario no ha iniciado sesión, redirige a la página de inicio de sesión
        return redirect(reverse('login'))  # Ajusta 'login' al nombre de la URL de tu página de inicio de sesión
    else:
        # Renderiza el archivo HTML o crea el contenido HTML aquí
        return render(request, 'audiovisuals_stock/calendar.html')