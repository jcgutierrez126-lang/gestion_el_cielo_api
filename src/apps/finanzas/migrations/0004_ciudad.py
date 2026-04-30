from django.db import migrations, models
import django.db.models.deletion


def migrate_ciudades(apps, schema_editor):
    Proveedor = apps.get_model('finanzas', 'Proveedor')
    Ciudad = apps.get_model('finanzas', 'Ciudad')
    cache = {}
    for proveedor in Proveedor.objects.filter(ciudad_old__isnull=False).exclude(ciudad_old=''):
        nombre = proveedor.ciudad_old.strip()
        if not nombre:
            continue
        if nombre not in cache:
            obj, _ = Ciudad.objects.get_or_create(nombre=nombre)
            cache[nombre] = obj
        proveedor.ciudad_fk = cache[nombre]
        proveedor.save(update_fields=['ciudad_fk'])


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0003_remove_vale_cuenta_remove_no_aplica_categoria'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ciudad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Fecha de actualización')),
                ('status', models.BooleanField(default=True, verbose_name='Estado')),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
            ],
            options={
                'verbose_name': 'Ciudad',
                'verbose_name_plural': 'Ciudades',
                'db_table': 'ciudades',
                'ordering': ['nombre'],
                'abstract': False,
            },
        ),
        migrations.RenameField(
            model_name='proveedor',
            old_name='ciudad',
            new_name='ciudad_old',
        ),
        migrations.AddField(
            model_name='proveedor',
            name='ciudad_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proveedores',
                to='finanzas.ciudad',
                verbose_name='Ciudad',
            ),
        ),
        migrations.RunPython(migrate_ciudades, migrations.RunPython.noop),
        migrations.RemoveField(model_name='proveedor', name='ciudad_old'),
        migrations.RenameField(model_name='proveedor', old_name='ciudad_fk', new_name='ciudad'),
    ]
