from django.db import migrations


def sync_ingresos(apps, schema_editor):
    VentaCafe = apps.get_model('produccion', 'VentaCafe')
    VentaBanano = apps.get_model('produccion', 'VentaBanano')
    Ingreso = apps.get_model('finanzas', 'Ingreso')

    for venta in VentaCafe.objects.select_related('tipo_cafe', 'cuenta_destino').all():
        tipo_nombre = venta.tipo_cafe.nombre if venta.tipo_cafe_id else ""
        origen = f"venta_cafe:{venta.id}"
        Ingreso.objects.update_or_create(
            origen=origen,
            defaults={
                "fecha": venta.fecha,
                "descripcion": f"Venta café — {tipo_nombre} | {venta.comprador}",
                "valor": venta.valor_neto,
                "cuenta_destino": venta.cuenta_destino,
            },
        )

    for venta in VentaBanano.objects.select_related('tipo_platano', 'cuenta_destino').all():
        tipo_nombre = venta.tipo_platano.nombre if venta.tipo_platano_id else ""
        origen = f"venta_banano:{venta.id}"
        Ingreso.objects.update_or_create(
            origen=origen,
            defaults={
                "fecha": venta.fecha,
                "descripcion": f"Venta banano — {tipo_nombre}",
                "valor": venta.valor_total,
                "cuenta_destino": venta.cuenta_destino,
            },
        )


def reverse_sync(apps, schema_editor):
    Ingreso = apps.get_model('finanzas', 'Ingreso')
    Ingreso.objects.filter(origen__startswith='venta_cafe:').delete()
    Ingreso.objects.filter(origen__startswith='venta_banano:').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0005_tipos_maestros_migrate'),
        ('finanzas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(sync_ingresos, reverse_sync),
    ]
