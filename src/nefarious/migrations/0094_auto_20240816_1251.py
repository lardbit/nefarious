# Generated by Django 3.0.2 on 2024-08-16 12:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nefarious', '0093_auto_20240816_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='watchmovie',
            name='quality_profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='nefarious.QualityProfile'),
        ),
        migrations.AlterField(
            model_name='watchtvseasonrequest',
            name='quality_profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='nefarious.QualityProfile'),
        ),
        migrations.AlterField(
            model_name='watchtvshow',
            name='quality_profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='nefarious.QualityProfile'),
        ),
    ]
