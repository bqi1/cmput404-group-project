# Generated by Django 3.1.7 on 2021-03-05 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firstapp', '0002_auto_20210305_0943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='consistent_id',
            field=models.TextField(blank=True, max_length=20, primary_key=True, serialize=False),
        ),
    ]
