from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('perfil/', views.view_profile, name='view_profile'),
    path('perfil/editar/', views.edit_profile, name='edit_profile'),
    path('crear-material/', views.subir_material, name='crear_material'),
    path('list-material/', views.lista_materiales, name='list_material'),
    path('material/<int:material_id>/', views.detalle_material, name='detalle_material'),
    path('editar-material/<int:material_id>/', views.editar_material, name='editar_material'),
    path('extraer/<int:material_id>/', views.extraer_material, name='extraer_material'),
    path('material/<int:material_id>/log/', views.log_material, name='log_material'),
    path('agregar-tipo-material/', views.agregar_tipo_material, name='agregar_tipo_material'),
    path('agregar-proveedor/', views.agregar_proveedor, name='agregar_proveedor'),
    path('saldar-deuda/<int:deuda_id>/', views.saldar_deuda, name='saldar_deuda'),
    path('calendar/', views.calendar, name='calendar'),
    path('', views.home, name='home'),  # Ruta para la página de inicio
]
handler404 = 'audiovisuals_stock.views.error_404'  # Ajusta esto a tu vista personalizada