# Generated by Django 3.2.5 on 2021-08-05 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0008_auto_20210805_1842'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customers',
            name='orders',
            field=models.ManyToManyField(related_name='related_customer', to='mainapp.Orders', verbose_name='Заказы покупателя'),
        ),
    ]