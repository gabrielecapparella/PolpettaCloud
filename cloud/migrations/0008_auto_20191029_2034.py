# Generated by Django 2.2.6 on 2019-10-29 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0007_auto_20191022_2003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gdrive_index',
            name='gdrive_id',
            field=models.CharField(default='', max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='gdrive_index',
            name='parent_gdrive_id',
            field=models.CharField(default='', max_length=256, null=True),
        ),
    ]