# Generated by Django 5.1.1 on 2024-09-30 10:01

from django.db import migrations


def seed_learnings_with_model_files(apps, schema_editor):
    Learning = apps.get_model('ebigkasLearnings', 'Learning')

    # Model 1 learnings
    Learning.objects.create(title='blank', action_model=1, model_file_path='MyModels/models 1/models 1.h5')
    Learning.objects.create(title='goodbye', action_model=1, model_file_path='MyModels/models 1/models 1.h5')
    Learning.objects.create(title='how are you', action_model=1, model_file_path='MyModels/models 1/models 1.h5')
    Learning.objects.create(title="I'm fine", action_model=1, model_file_path='MyModels/models 1/models 1.h5')

    # Model 2 learnings
    Learning.objects.create(title='blank', action_model=2, model_file_path='MyModels/models 2/models 2.h5')
    Learning.objects.create(title="I'm not fine", action_model=2, model_file_path='MyModels/models 2/models 2.h5')
    Learning.objects.create(title="I love you", action_model=2, model_file_path='MyModels/models 2/models 2.h5')
    Learning.objects.create(title='maybe', action_model=2, model_file_path='MyModels/models 2/models 2.h5')

    # Model 3 learnings
    Learning.objects.create(title='blank', action_model=3, model_file_path='MyModels/models 3/models 3.h5')
    Learning.objects.create(title='sorry', action_model=3, model_file_path='MyModels/models 3/models 3.h5')
    Learning.objects.create(title='no', action_model=3, model_file_path='MyModels/models 3/models 3.h5')
    Learning.objects.create(title='thank you', action_model=3, model_file_path='MyModels/models 3/models 3.h5')

    # Model 4 learnings
    Learning.objects.create(title='blank', action_model=4, model_file_path='MyModels/models 4/models 4.h5')
    Learning.objects.create(title='take care', action_model=4, model_file_path='MyModels/models 4/models 4.h5')
    Learning.objects.create(title='when', action_model=4, model_file_path='MyModels/models 4/models 4.h5')
    Learning.objects.create(title='what', action_model=4, model_file_path='MyModels/models 4/models 4.h5')

    # Model 5 learnings
    Learning.objects.create(title='blank', action_model=5, model_file_path='MyModels/models 5/models 5.h5')
    Learning.objects.create(title='yes', action_model=5, model_file_path='MyModels/models 5/models 5.h5')
    Learning.objects.create(title='where', action_model=5, model_file_path='MyModels/models 5/models 5.h5')
    Learning.objects.create(title='understand', action_model=5, model_file_path='MyModels/models 5/models 5.h5')


class Migration(migrations.Migration):

    dependencies = [
        ('ebigkasLearnings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_learnings_with_model_files),
    ]