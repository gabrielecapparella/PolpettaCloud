# Generated by Django 3.1.2 on 2020-12-12 12:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GooglePhotosSync',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('g_token', models.CharField(default='', max_length=256, null=True)),
                ('g_refresh_token', models.CharField(default='', max_length=256, null=True)),
                ('pics_folder', models.CharField(max_length=128)),
                ('last_pic', models.CharField(default='', max_length=256, null=True)),
                ('last_sync', models.DateTimeField()),
            ],
        ),
        migrations.RemoveField(
            model_name='clouduser',
            name='pics_default',
        ),
        migrations.AlterField(
            model_name='clouduser',
            name='root_path',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='clouduser',
            name='trash_path',
            field=models.CharField(max_length=128),
        ),
        migrations.DeleteModel(
            name='GoogleTokens',
        ),
        migrations.AddField(
            model_name='googlephotossync',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]