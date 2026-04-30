from django.db import migrations, models
import django.db.models.deletion


def migrate_variedades(apps, schema_editor):
    Lote = apps.get_model('produccion', 'Lote')
    VariedadLote = apps.get_model('produccion', 'VariedadLote')
    cache = {}
    for lote in Lote.objects.filter(variedad_old__isnull=False).exclude(variedad_old=''):
        nombre = lote.variedad_old.strip()
        if not nombre:
            continue
        if nombre not in cache:
            obj, _ = VariedadLote.objects.get_or_create(nombre=nombre)
            cache[nombre] = obj
        lote.variedad_fk = cache[nombre]
        lote.save(update_fields=['variedad_fk'])


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0006_sync_ingresos_ventas'),
    ]

    operations = [
        migrations.CreateModel(
            name='VariedadLote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Fecha de actualización')),
                ('status', models.BooleanField(default=True, verbose_name='Estado')),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
            ],
            options={
                'verbose_name': 'Variedad de Lote',
                'verbose_name_plural': 'Variedades de Lote',
                'db_table': 'variedades_lote',
                'ordering': ['nombre'],
                'abstract': False,
            },
        ),
        migrations.RenameField(
            model_name='lote',
            old_name='variedad',
            new_name='variedad_old',
        ),
        migrations.AddField(
            model_name='lote',
            name='variedad_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lotes',
                to='produccion.variedadlote',
                verbose_name='Variedad',
            ),
        ),
        migrations.RunPython(migrate_variedades, migrations.RunPython.noop),
        migrations.RemoveField(model_name='lote', name='variedad_old'),
        migrations.RenameField(model_name='lote', old_name='variedad_fk', new_name='variedad'),
    ]
