# Generated by Django 5.1 on 2024-09-02 06:17

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ebigkasAPP', '0006_room_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecentCalls',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_initiator', models.BooleanField(default=False)),
                ('duration', models.DurationField(default=datetime.timedelta)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('call_with', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calls', to=settings.AUTH_USER_MODEL)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recent_calls', to='ebigkasAPP.room')),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['timestamp'], name='ebigkasAPP__timesta_f6bcdc_idx')],
            },
        ),
    ]