# audiovisuals_stock/forms.py
from django import forms
from .models import UserProfile  # Asegúrate de importar tu modelo de perfil
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Material, TipoMaterial, Proveedor, MaterialLog


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'nombre']  # Lista los campos que los usuarios pueden editar

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'nombre')  # Agrega aquí los campos que desees en el formulario de registro

    def clean_password2(self):
        # Verifica que las contraseñas coincidan
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def save(self, commit=True):
        # Guarda la contraseña de manera segura
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
    
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nombre']  # Lista de campos que deseas que los usuarios puedan editar



class TipoMaterialForm(forms.ModelForm):
    class Meta:
        model = TipoMaterial
        fields = ['nombre']

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre']


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['referencia', 'nombre', 'cantidad', 'tipo', 'fecha_compra', 'proveedor', 'numero_serie']
        tipo = forms.ModelChoiceField(queryset=TipoMaterial.objects.all(), empty_label="Selecciona un Tipo")
        proveedor = forms.ModelChoiceField(queryset=Proveedor.objects.all(), empty_label="Selecciona un Proveedor")

class MaterialEditForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['referencia', 'nombre', 'cantidad', 'tipo', 'fecha_compra', 'proveedor', 'numero_serie']


class ExtraccionMaterialForm(forms.ModelForm):
    class Meta:
        model = MaterialLog
        fields = ['cantidad_extraida']
        labels = {
            'cantidad_extraida': 'Cantidad a extraer',  # Define las etiquetas personalizadas aquí
            # Otras etiquetas personalizadas para otros campos
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cantidad_extraida'].widget = forms.NumberInput(attrs={'min': 1})