# Generated by Django 3.1.7 on 2021-03-05 00:07

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('firstapp', '0005_auto_20210304_1619'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]