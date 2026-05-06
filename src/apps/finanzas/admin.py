from django.contrib import admin
from .models import Cuenta, Proveedor, Egreso, Ingreso, Transaccion

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "saldo_inicial")
    list_filter = ("tipo",)
    search_fields = ("nombre",)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "telefono", "celular", "ciudad")
    search_fields = ("nombre", "cedula_nit")

@admin.register(Egreso)
class EgresoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "nombre", "categoria", "valor", "cuenta", "estado")
    list_filter = ("categoria", "cuenta", "estado")
    search_fields = ("nombre", "descripcion")
    date_hierarchy = "fecha"

@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "descripcion", "valor", "cuenta_destino")
    list_filter = ("cuenta_destino",)
    search_fields = ("descripcion", "origen")
    date_hierarchy = "fecha"

@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ("fecha", "cuenta_origen", "cuenta_destino", "valor")
    list_filter = ("cuenta_origen", "cuenta_destino")
    date_hierarchy = "fecha"

