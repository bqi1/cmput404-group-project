# Generated by Django 3.1.7 on 2021-03-04 19:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firstapp', '0003_auto_20210304_1250'),
    ]

    operations = [
        migrations.RenameField(
            model_name='author',
            old_name='user',
            new_name='username',
        ),
    ]