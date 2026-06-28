# Generated manually to add extracted_by field

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('resume_analyzer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='resumeanalysis',
            name='extracted_by',
            field=models.CharField(choices=[('AI', 'AI'), ('Code', 'Code')], default='Code', max_length=10),
        ),
    ]
