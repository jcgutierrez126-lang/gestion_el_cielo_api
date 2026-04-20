from django.db import migrations, models
import django.db.models.deletion


def migrate_lote(apps, schema_editor):
    ControlSemanal = apps.get_model('nomina', 'ControlSemanal')
    Lote = apps.get_model('produccion', 'Lote')

    lote_cache = {l.nombre.lower(): l for l in Lote.objects.all()}

    for cs in ControlSemanal.objects.exclude(lote_str__isnull=True).exclude(lote_str=""):
        nombre = (cs.lote_str or "").strip().lower()
        if not nombre:
            continue
        # exact match first
        lote = lote_cache.get(nombre)
        # partial match fallback
        if not lote:
            lote = next((v for k, v in lote_cache.items() if nombre in k or k in nombre), None)
        if lote:
            cs.lote_fk = lote
            cs.save(update_fields=['lote_fk'])


class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0003_tipolabor_tipocobro_status'),
        ('produccion', '0001_initial'),
    ]

    operations = [
        # 1. Rename old CharField
        migrations.RenameField('ControlSemanal', 'lote', 'lote_str'),

        # 2. Add nullable FK
        migrations.AddField(
            model_name='ControlSemanal',
            name='lote_fk',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='produccion.lote', verbose_name='Lote',
            ),
        ),

        # 3. Migrate data
        migrations.RunPython(migrate_lote, migrations.RunPython.noop),

        # 4. Drop old CharField
        migrations.RemoveField('ControlSemanal', 'lote_str'),

        # 5. Rename FK to final name
        migrations.RenameField('ControlSemanal', 'lote_fk', 'lote'),
    ]
