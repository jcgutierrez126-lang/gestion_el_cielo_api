from django.contrib import admin
from .models import (
    TipoBanano, TipoCafe,
    Lote, VentaCafe, VentaCafeTostado, Floracion, MezclaAbono, MezclaAbonoFertilizante, VentaBanano,
)


@admin.register(TipoBanano)
class TipoBananoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "status")
    list_filter = ("status",)
    search_fields = ("nombre",)


@admin.register(TipoCafe)
class TipoCafeAdmin(admin.ModelAdmin):
    list_display = ("nombre", "status")
    list_filter = ("status",)
    search_fields = ("nombre",)


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "abreviatura", "variedad", "año_siembra", "num_arboles", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "abreviatura", "variedad")


@admin.register(VentaCafe)
class VentaCafeAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo_cafe", "kilos", "cargas", "precio_kilo", "valor_neto", "comprador")
    list_filter = ("tipo_cafe", "comprador")
    search_fields = ("comprador", "facturado_a")
    date_hierarchy = "fecha"


@admin.register(VentaCafeTostado)
class VentaCafeTostadoAdmin(admin.ModelAdmin):
    list_display = ("fecha_venta", "cliente", "presentacion", "tipo_cafe", "cantidad", "valor")
    list_filter = ("presentacion", "tipo_cafe", "seleccionado")
    search_fields = ("cliente",)
    date_hierarchy = "fecha_venta"


@admin.register(Floracion)
class FloracionAdmin(admin.ModelAdmin):
    list_display = ("fecha", "lote", "calidad")
    list_filter = ("lote", "calidad")
    date_hierarchy = "fecha"


class MezclaAbonoFertilizanteInline(admin.TabularInline):
    model = MezclaAbonoFertilizante
    extra = 1
    fields = ("fertilizante", "num_bultos", "precio_bulto")


@admin.register(MezclaAbono)
class MezclaAbonoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "lote", "formula", "num_arboles", "gramos_por_arbol", "costo_total")
    list_filter = ("lote",)
    date_hierarchy = "fecha"
    inlines = [MezclaAbonoFertilizanteInline]


@admin.register(MezclaAbonoFertilizante)
class MezclaAbonoFertilizanteAdmin(admin.ModelAdmin):
    list_display = ("mezcla", "fertilizante", "num_bultos", "precio_bulto")


@admin.register(VentaBanano)
class VentaBananoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo_platano", "kilos", "precio_kilo", "valor_total", "cuenta_destino")
    list_filter = ("tipo_platano", "cuenta_destino")
    date_hierarchy = "fecha"
