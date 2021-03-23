# Generated by Django 3.1.7 on 2021-03-23 03:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
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
                ('consistent_id', models.TextField(blank=True, editable=False, max_length=20, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Author_Privacy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_id', models.PositiveIntegerField(default=0)),
                ('user_id', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('post_id', models.PositiveIntegerField(default=0, primary_key=True, serialize=False)),
                ('user_id', models.PositiveIntegerField(default=0)),
                ('title', models.CharField(default='', max_length=20)),
                ('description', models.CharField(default='', max_length=30)),
                ('markdown', models.BooleanField(default=False)),
                ('content', models.TextField(blank=True, max_length=500)),
                ('image', models.BinaryField(default=b'')),
                ('privfriends', models.BooleanField(default=False)),
                ('tstamp', models.CharField(default='', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='PublicImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField()),
                ('image', models.ImageField(upload_to='images/')),
            ],
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('UsersNeedAuthentication', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='PostLikes',
            fields=[
                ('like_id', models.AutoField(primary_key=True, serialize=False)),
                ('from_user', models.IntegerField(blank=True, null=True)),
                ('to_user', models.IntegerField(blank=True, null=True)),
                ('post_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='firstapp.post')),
            ],
        ),
    ]
