# Generated by Django 5.2.1 on 2025-06-07 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produk', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaksi',
            name='jumlah',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
    ]
