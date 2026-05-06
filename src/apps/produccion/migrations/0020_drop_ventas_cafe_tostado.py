from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('produccion', '0019_observacion_origen'),
    ]

    operations = [
        migrations.DeleteModel(
            name='VentaCafeTostado',
        ),
    ]
