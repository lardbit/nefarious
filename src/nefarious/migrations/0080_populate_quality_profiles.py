from django.db import migrations, transaction
from nefarious.quality import PROFILES


def populate_quality_profile(apps, schema_editor):
    NefariousSettings = apps.get_model('nefarious', 'NefariousSettings')
    QualityProfile = apps.get_model('nefarious', 'QualityProfile')

    nefarious_settings = NefariousSettings.objects.all().first()

    # copy values from old field
    for profile in PROFILES:
        QualityProfile.objects.create(
            name=profile,
            quality=profile,
        )

    if not nefarious_settings:
        return

    quality_profile_tv = QualityProfile.objects.filter(quality=nefarious_settings.quality_profile_tv).first()
    quality_profile_movies = QualityProfile.objects.filter(quality=nefarious_settings.quality_profile_movies).first()

    nefarious_settings.quality_profile_tv_default = quality_profile_tv
    nefarious_settings.quality_profile_movies_default = quality_profile_movies

    with transaction.atomic():
        nefarious_settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('nefarious', '0079_auto_20240728_1312'),
    ]

    operations = [
        migrations.RunPython(populate_quality_profile, reverse_code=lambda a, b: None),
    ]
