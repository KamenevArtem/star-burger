# Generated by Django 3.2.15 on 2023-05-17 22:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0040_transfer_prices'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('A', 'Принят'), ('P', 'Готовится'), ('D', 'Передан в доставку'), ('DN', 'Заказ выполнен')], db_index=True, default='A', max_length=30, verbose_name='Статус заказа'),
        ),
        migrations.AlterField(
            model_name='orderelement',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Цена'),
        ),
    ]
