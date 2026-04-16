from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('integraciones', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pedido',
            old_name='observaciones_corona',
            new_name='observaciones_cielo',
        ),
    ]
