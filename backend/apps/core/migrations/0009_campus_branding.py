from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_attendancedevice_hardware_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="campus",
            name="logo_url",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="campus",
            name="logo_alt_text",
            field=models.CharField(blank=True, max_length=160),
        ),
    ]
