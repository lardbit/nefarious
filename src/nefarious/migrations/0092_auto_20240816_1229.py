# Generated by Django 3.0.2 on 2024-08-16 12:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nefarious', '0091_auto_20240815_2159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nefarioussettings',
            name='quality_profile_movies',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='quality_profile_movies_default', to='nefarious.QualityProfile'),
        ),
        migrations.AlterField(
            model_name='nefarioussettings',
            name='quality_profile_tv',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='quality_profile_tv_default', to='nefarious.QualityProfile'),
        ),
    ]