from django.db import migrations, models


class Migration(migrations.Migration):
    """Move Observacion state from finanzas to produccion. Table already exists — no DB ops."""

    dependencies = [
        ('produccion', '0017_ventacafe_cargas_decimal_places_6'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Observacion',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('status', models.BooleanField(default=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('fecha', models.DateField(db_index=True, verbose_name='Fecha')),
                        ('observacion', models.TextField(verbose_name='Observación')),
                    ],
                    options={
                        'verbose_name': 'Observación',
                        'verbose_name_plural': 'Observaciones',
                        'db_table': 'observaciones',
                        'ordering': ['-fecha'],
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
