from django.db import migrations, models
import django.db.models.deletion

TIPOS_LABOR = [
    ('recoleccion',          'Recolección'),
    ('guadana',              'Guadaña'),
    ('abono',                'Abono'),
    ('arriero',              'Arriero'),
    ('auxilio_labor',        'Auxilio Labor'),
    ('auxilio_transporte',   'Auxilio Transporte'),
    ('banano',               'Banano'),
    ('broca',                'Broca'),
    ('control_plagas',       'Control plagas'),
    ('cosecha',              'Cosecha'),
    ('deshojada',            'Deshojada'),
    ('deschuponar',          'Deschuponar'),
    ('desbejucar',           'Desbejucar'),
    ('embolsada',            'Embolsada'),
    ('varios',               'Varios'),
    ('siembra',              'Siembra'),
    ('permiso',              'Permiso'),
    ('nomina',               'Nómina'),
    ('contrato',             'Contrato'),
]

TIPOS_COBRO = [
    ('kilos',    'Kilos'),
    ('jornal',   'Jornal'),
    ('nomina',   'Nómina'),
    ('contrato', 'Contrato'),
]

# Mapping from old CharField key → display name used in TipoLabor.nombre
KEY_TO_LABOR = {k: v for k, v in TIPOS_LABOR}
KEY_TO_COBRO = {k: v for k, v in TIPOS_COBRO}


def populate_masters(apps, schema_editor):
    TipoLabor = apps.get_model('nomina', 'TipoLabor')
    TipoCobro = apps.get_model('nomina', 'TipoCobro')
    for _, nombre in TIPOS_LABOR:
        TipoLabor.objects.get_or_create(nombre=nombre)
    for _, nombre in TIPOS_COBRO:
        TipoCobro.objects.get_or_create(nombre=nombre)


def migrate_control_semanal(apps, schema_editor):
    ControlSemanal = apps.get_model('nomina', 'ControlSemanal')
    TipoLabor = apps.get_model('nomina', 'TipoLabor')
    TipoCobro = apps.get_model('nomina', 'TipoCobro')

    labor_cache = {t.nombre: t for t in TipoLabor.objects.all()}
    cobro_cache = {t.nombre: t for t in TipoCobro.objects.all()}

    # fallback: create unknown types on the fly
    def get_labor(key):
        nombre = KEY_TO_LABOR.get(key, key)
        if nombre not in labor_cache:
            obj, _ = TipoLabor.objects.get_or_create(nombre=nombre)
            labor_cache[nombre] = obj
        return labor_cache[nombre]

    def get_cobro(key):
        nombre = KEY_TO_COBRO.get(key, key)
        if nombre not in cobro_cache:
            obj, _ = TipoCobro.objects.get_or_create(nombre=nombre)
            cobro_cache[nombre] = obj
        return cobro_cache[nombre]

    for cs in ControlSemanal.objects.all():
        cs.tipo_labor_fk = get_labor(cs.tipo_labor_str)
        cs.tipo_cobro_fk = get_cobro(cs.tipo_cobro_str)
        cs.save(update_fields=['tipo_labor_fk', 'tipo_cobro_fk'])


class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0001_initial'),
    ]

    operations = [
        # 1. Create master tables
        migrations.CreateModel(
            name='TipoLabor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={'db_table': 'tipos_labor', 'ordering': ['nombre'],
                     'verbose_name': 'Tipo de labor', 'verbose_name_plural': 'Tipos de labor'},
        ),
        migrations.CreateModel(
            name='TipoCobro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={'db_table': 'tipos_cobro', 'ordering': ['nombre'],
                     'verbose_name': 'Tipo de cobro', 'verbose_name_plural': 'Tipos de cobro'},
        ),

        # 2. Populate master tables
        migrations.RunPython(populate_masters, migrations.RunPython.noop),

        # 3. Rename old CharFields so they don't collide with the new FK names
        migrations.RenameField('ControlSemanal', 'tipo_labor', 'tipo_labor_str'),
        migrations.RenameField('ControlSemanal', 'tipo_cobro', 'tipo_cobro_str'),

        # 4. Add nullable FK columns
        migrations.AddField(
            model_name='ControlSemanal',
            name='tipo_labor_fk',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='nomina.tipolabor', verbose_name='Tipo labor',
            ),
        ),
        migrations.AddField(
            model_name='ControlSemanal',
            name='tipo_cobro_fk',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='nomina.tipocobro', verbose_name='Tipo cobro',
            ),
        ),

        # 5. Migrate existing data
        migrations.RunPython(migrate_control_semanal, migrations.RunPython.noop),

        # 6. Drop old string columns
        migrations.RemoveField('ControlSemanal', 'tipo_labor_str'),
        migrations.RemoveField('ControlSemanal', 'tipo_cobro_str'),

        # 7. Rename FK columns to final names
        migrations.RenameField('ControlSemanal', 'tipo_labor_fk', 'tipo_labor'),
        migrations.RenameField('ControlSemanal', 'tipo_cobro_fk', 'tipo_cobro'),

        # 8. Make FKs non-nullable
        migrations.AlterField(
            model_name='ControlSemanal',
            name='tipo_labor',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='nomina.tipolabor', verbose_name='Tipo labor',
            ),
        ),
        migrations.AlterField(
            model_name='ControlSemanal',
            name='tipo_cobro',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='nomina.tipocobro', verbose_name='Tipo cobro',
            ),
        ),

        # 9. Update index that referenced old tipo_labor string field
        migrations.AlterIndexTogether(
            name='ControlSemanal',
            index_together=set(),
        ),
    ]
