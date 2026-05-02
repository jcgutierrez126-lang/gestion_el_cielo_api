from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.finanzas.models import Ingreso


def _sync_ingreso_cafe(venta):
    origen = f"venta_cafe:{venta.id}"
    tipo_nombre = venta.tipo_cafe.nombre if venta.tipo_cafe_id else ""
    descripcion = f"Venta café — {tipo_nombre} | {venta.comprador}"
    defaults = {
        "fecha": venta.fecha,
        "descripcion": descripcion,
        "valor": venta.valor_neto,
        "cuenta_destino": venta.cuenta_destino,
        "origen": origen,
    }
    Ingreso.objects.update_or_create(origen=origen, defaults=defaults)


def _sync_ingreso_banano(venta):
    origen = f"venta_banano:{venta.id}"
    tipo_nombre = venta.tipo_platano.nombre if venta.tipo_platano_id else ""
    descripcion = f"Venta banano — {tipo_nombre}"
    defaults = {
        "fecha": venta.fecha,
        "descripcion": descripcion,
        "valor": venta.valor_total,
        "cuenta_destino": venta.cuenta_destino,
        "origen": origen,
    }
    Ingreso.objects.update_or_create(origen=origen, defaults=defaults)


def _sync_ingreso_tostado(venta):
    origen = f"venta_tostado:{venta.id}"
    descripcion = f"Venta café tostado — {venta.get_presentacion_display()} | {venta.cliente or 'Sin cliente'}"
    defaults = {
        "fecha": venta.fecha_venta,
        "descripcion": descripcion,
        "valor": venta.valor,
        "cuenta_destino": venta.cuenta_destino,
        "origen": origen,
    }
    Ingreso.objects.update_or_create(origen=origen, defaults=defaults)


@receiver(post_save, sender="produccion.VentaCafe")
def on_venta_cafe_save(sender, instance, **kwargs):
    _sync_ingreso_cafe(instance)


@receiver(post_save, sender="produccion.VentaBanano")
def on_venta_banano_save(sender, instance, **kwargs):
    _sync_ingreso_banano(instance)


@receiver(post_save, sender="produccion.VentaCafeTostado")
def on_venta_tostado_save(sender, instance, **kwargs):
    _sync_ingreso_tostado(instance)


@receiver(post_delete, sender="produccion.VentaCafe")
def on_venta_cafe_delete(sender, instance, **kwargs):
    Ingreso.objects.filter(origen=f"venta_cafe:{instance.id}").delete()


@receiver(post_delete, sender="produccion.VentaBanano")
def on_venta_banano_delete(sender, instance, **kwargs):
    Ingreso.objects.filter(origen=f"venta_banano:{instance.id}").delete()


@receiver(post_delete, sender="produccion.VentaCafeTostado")
def on_venta_tostado_delete(sender, instance, **kwargs):
    Ingreso.objects.filter(origen=f"venta_tostado:{instance.id}").delete()
