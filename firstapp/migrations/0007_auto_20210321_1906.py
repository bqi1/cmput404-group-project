# Generated by Django 2.1.7 on 2021-03-21 19:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firstapp', '0006_auto_20210321_1843'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='private_to_friends',
            new_name='privfriends',
        ),
    ]