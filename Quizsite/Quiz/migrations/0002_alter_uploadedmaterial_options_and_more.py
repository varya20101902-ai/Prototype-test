# Создано Django 6.0.3 2026-05-09 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Quiz', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='uploadedmaterial',
            options={'verbose_name': 'загруженный материал', 'verbose_name_plural': 'загруженные материалы'},
        ),
        migrations.AlterField(
            model_name='uploadedmaterial',
            name='material',
            field=models.FileField(upload_to='media/', verbose_name='Учебный материал'),
        ),
        migrations.AlterField(
            model_name='uploadedmaterial',
            name='uploaded_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки'),
        ),
    ]
