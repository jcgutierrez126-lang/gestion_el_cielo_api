from django.contrib import admin
from apps.integraciones.models import (
    Pedido,
    SuplosToken,
    TrazabilidadPedido,
    LogConsulta,
    CorreoAutorizado,
    CorreoProcesado,
)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        'documento_compras',
        'posicion',
        'razon_social',
        'estado_pedido',
        'fecha_entrega',
        'fuente_supplos',
        'fuente_graph',
        'created_at'
    ]
    list_filter = ['estado_pedido', 'fuente_supplos', 'fuente_graph', 'status']
    search_fields = ['documento_compras', 'razon_social', 'material', 'comprador']
    readonly_fields = ['created_at', 'updated_at', 'ultima_sincronizacion', 'datos_raw_supplos']
    ordering = ['-created_at']

    fieldsets = (
        ('Identificacion', {
            'fields': ('documento_compras', 'posicion', 'proveedor_centro_suministrador', 'razon_social')
        }),
        ('Compra', {
            'fields': ('comprador', 'organizacion_compras', 'planta')
        }),
        ('Material', {
            'fields': ('material', 'texto_breve', 'cantidad_pedido', 'por_entregar', 'precio_neto')
        }),
        ('Fechas', {
            'fields': ('fecha_entrega', 'fecha_programada')
        }),
        ('Estado', {
            'fields': ('estado_pedido', 'motivo', 'observaciones', 'estado', 'observaciones_corona')
        }),
        ('Metadatos', {
            'fields': ('fuente_supplos', 'fuente_graph', 'ultima_sincronizacion', 'status'),
            'classes': ('collapse',)
        }),
        ('Datos Crudos', {
            'fields': ('datos_raw_supplos',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TrazabilidadPedido)
class TrazabilidadPedidoAdmin(admin.ModelAdmin):
    list_display = [
        'pedido',
        'fuente',
        'estado_anterior',
        'estado_nuevo',
        'fecha_registro'
    ]
    list_filter = ['fuente', 'fecha_registro']
    search_fields = ['pedido__documento_compras', 'observaciones']
    readonly_fields = ['fecha_registro', 'datos_raw']
    ordering = ['-fecha_registro']


@admin.register(SuplosToken)
class SuplosTokenAdmin(admin.ModelAdmin):
    list_display = ['id', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active']
    readonly_fields = ['access_token', 'created_at']


@admin.register(LogConsulta)
class LogConsultaAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'respuesta_exitosa', 'tiempo_respuesta_ms', 'usuario', 'created_at']
    list_filter = ['tipo', 'respuesta_exitosa']
    readonly_fields = ['parametros', 'created_at']
    ordering = ['-created_at']


@admin.register(CorreoAutorizado)
class CorreoAutorizadoAdmin(admin.ModelAdmin):
    list_display = ['email', 'nombre', 'es_buzon_principal', 'activo', 'created_at']
    list_filter = ['activo', 'es_buzon_principal']
    search_fields = ['email', 'nombre']
    ordering = ['-es_buzon_principal', 'email']


@admin.register(CorreoProcesado)
class CorreoProcesadoAdmin(admin.ModelAdmin):
    list_display = ['subject', 'buzon', 'fecha_email', 'procesado_at']
    list_filter = ['buzon', 'procesado_at']
    search_fields = ['subject', 'email_id']
    readonly_fields = ['email_id', 'procesado_at']
    ordering = ['-procesado_at']
