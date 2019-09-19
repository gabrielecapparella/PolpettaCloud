# Generated by Django 2.2.3 on 2019-09-19 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0004_clouduser_pics_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='clouduser',
            name='g_refresh_token',
            field=models.CharField(default='', max_length=64),
        ),
        migrations.AddField(
            model_name='clouduser',
            name='g_token',
            field=models.CharField(default='', max_length=256),
        ),
        migrations.AddField(
            model_name='googlesync',
            name='album_id',
            field=models.CharField(default='', max_length=128),
        ),
        migrations.AlterField(
            model_name='clouduser',
            name='pics_default',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='clouduser',
            name='root_path',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='clouduser',
            name='trash_path',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='googlesync',
            name='path',
            field=models.CharField(max_length=128),
        ),
    ]