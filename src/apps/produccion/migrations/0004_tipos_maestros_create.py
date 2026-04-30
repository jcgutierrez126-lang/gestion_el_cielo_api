from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0003_lote_add_abreviatura'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoBanano',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Fecha de actualización')),
                ('status', models.BooleanField(default=True, verbose_name='Estado')),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
            ],
            options={
                'verbose_name': 'Tipo de Banano',
                'verbose_name_plural': 'Tipos de Banano',
                'db_table': 'tipos_banano',
                'ordering': ['nombre'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TipoCafe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Fecha de actualización')),
                ('status', models.BooleanField(default=True, verbose_name='Estado')),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
            ],
            options={
                'verbose_name': 'Tipo de Café',
                'verbose_name_plural': 'Tipos de Café',
                'db_table': 'tipos_cafe',
                'ordering': ['nombre'],
                'abstract': False,
            },
        ),
        # Renombrar campos viejos (CharField) para liberar el nombre
        migrations.RenameField(
            model_name='ventabanano',
            old_name='tipo_platano',
            new_name='tipo_platano_old',
        ),
        migrations.RenameField(
            model_name='ventacafe',
            old_name='tipo_cafe',
            new_name='tipo_cafe_old',
        ),
        # Agregar nuevas FKs (nullable por ahora para la data migration)
        migrations.AddField(
            model_name='ventabanano',
            name='tipo_platano',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='produccion.tipobanano',
                verbose_name='Tipo',
            ),
        ),
        migrations.AddField(
            model_name='ventacafe',
            name='tipo_cafe',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='produccion.tipocafe',
                verbose_name='Tipo de café',
            ),
        ),
    ]
