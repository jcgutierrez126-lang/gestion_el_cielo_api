from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0002_alter_ventabanano_tipo_platano'),
    ]

    operations = [
        migrations.AddField(
            model_name='lote',
            name='abreviatura',
            field=models.CharField(blank=True, null=True, max_length=20, unique=True, verbose_name='Abreviatura'),
        ),
    ]
