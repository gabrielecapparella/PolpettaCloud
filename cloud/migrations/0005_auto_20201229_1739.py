# Generated by Django 3.1.2 on 2020-12-29 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0004_googlephotossync_last_sync_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='googlephotossync',
            name='last_sync_result',
            field=models.BooleanField(null=True),
        ),
    ]