# Generated by Django 2.2.3 on 2019-09-15 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0003_googlesync_is_dir'),
    ]

    operations = [
        migrations.AddField(
            model_name='clouduser',
            name='pics_default',
            field=models.CharField(default='Pictures', max_length=32),
            preserve_default=False,
        ),
    ]
