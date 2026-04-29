from django.contrib import admin
from .models import TipoLabor, TipoCobro, Empleado, ControlSemanal, PrestamoEmpleado, ControlDiario, AbonoPrestamo

@admin.register(TipoLabor)
class TipoLaborAdmin(admin.ModelAdmin):
    list_display = ("nombre", "abreviatura", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "abreviatura")

@admin.register(TipoCobro)
class TipoCobroAdmin(admin.ModelAdmin):
    list_display = ("nombre", "abreviatura", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "abreviatura")

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "cedula", "labor", "jornal", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre_completo", "cedula")

@admin.register(ControlSemanal)
class ControlSemanalAdmin(admin.ModelAdmin):
    list_display = ("empleado", "fecha_inicio", "fecha_fin", "lote", "tipo_labor", "tipo_cobro", "jornales", "kilos", "valor")
    list_filter = ("fecha_inicio", "lote", "tipo_labor", "tipo_cobro")
    search_fields = ("empleado__nombre_completo",)
    date_hierarchy = "fecha_inicio"

@admin.register(ControlDiario)
class ControlDiarioAdmin(admin.ModelAdmin):
    list_display = ("semana_ref", "fecha", "dia", "nombre", "lote", "labor", "tipo_cobro", "cantidad", "valor")
    list_filter = ("semana_ref", "dia")
    search_fields = ("nombre", "lote", "labor")
    date_hierarchy = "fecha"

@admin.register(PrestamoEmpleado)
class PrestamoEmpleadoAdmin(admin.ModelAdmin):
    list_display = ("empleado", "fecha", "valor", "saldo", "concepto")
    list_filter = ("empleado",)
    search_fields = ("empleado__nombre_completo", "concepto")
    date_hierarchy = "fecha"

@admin.register(AbonoPrestamo)
class AbonoPrestamoAdmin(admin.ModelAdmin):
    list_display = ("prestamo", "fecha", "valor", "nota")
    date_hierarchy = "fecha"
