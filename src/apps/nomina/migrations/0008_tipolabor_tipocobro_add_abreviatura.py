from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomina', '0007_merge_20260421_0742'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipolabor',
            name='abreviatura',
            field=models.CharField(blank=True, null=True, max_length=20, unique=True, verbose_name='Abreviatura'),
        ),
        migrations.AddField(
            model_name='tipocobro',
            name='abreviatura',
            field=models.CharField(blank=True, null=True, max_length=20, unique=True, verbose_name='Abreviatura'),
        ),
    ]
