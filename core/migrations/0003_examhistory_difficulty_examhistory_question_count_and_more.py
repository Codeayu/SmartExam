# Generated by Django 5.2 on 2025-05-04 07:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_examhistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='examhistory',
            name='difficulty',
            field=models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], default='medium', max_length=20),
        ),
        migrations.AddField(
            model_name='examhistory',
            name='question_count',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='examhistory',
            name='specific_topics',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='SavedQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('answer_text', models.TextField()),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('exam_history', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_questions', to='core.examhistory')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_questions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
