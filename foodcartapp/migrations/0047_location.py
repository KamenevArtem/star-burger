# Generated by Django 3.2.15 on 2023-05-22 00:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_auto_20230520_2229'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(blank=True, max_length=100, unique=True, verbose_name='Адрес')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='Широта')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='Долгота')),
                ('created_at', models.DateField(verbose_name='Дата запроса')),
            ],
            options={
                'verbose_name': 'Геолокация',
                'verbose_name_plural': 'Геолокации',
            },
        ),
    ]
