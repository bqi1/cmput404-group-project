# Generated by Django 3.1.7 on 2021-03-05 16:43

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('firstapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('username', models.CharField(max_length=20)),
                ('github', models.URLField(blank=True)),
                ('github_username', models.TextField(blank=True, max_length=20)),
                ('host', models.TextField(blank=True, max_length=500)),
                ('authorized', models.BooleanField(default=True)),
                ('userid', models.PositiveIntegerField(default=0)),
                ('email', models.EmailField(default='example@gmail.com', max_length=254)),
                ('name', models.CharField(default='testname', max_length=20)),
                ('consistent_id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='PublicImages',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('img', models.ImageField(upload_to='image/')),
            ],
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UsersNeedAuthentication', models.BooleanField(default=False)),
            ],
        ),
        migrations.DeleteModel(
            name='UserCreation',
        ),
    ]
