# Generated by Django 5.1.1 on 2024-10-24 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ebigkasAPP', '0016_userprofile_bio'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='voice_preference',
            field=models.CharField(default='Male', max_length=7),
        ),
    ]