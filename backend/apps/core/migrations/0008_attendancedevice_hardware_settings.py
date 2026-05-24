from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_announcement_supportticket"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendancedevice",
            name="baud_rate",
            field=models.PositiveIntegerField(default=38400, validators=[MinValueValidator(1200), MaxValueValidator(921600)]),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="device_numeric_id",
            field=models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(999999)]),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="domain_name",
            field=models.CharField(blank=True, default="device.nialabs.in", max_length=180),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="heartbeat_seconds",
            field=models.PositiveIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(3600)]),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="local_port",
            field=models.PositiveIntegerField(default=5005, validators=[MinValueValidator(1), MaxValueValidator(65535)]),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="rs485_function",
            field=models.CharField(
                choices=[("software", "Software"), ("hardware", "Hardware"), ("disabled", "Disabled")],
                default="software",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="server_approval_required",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="server_ip",
            field=models.CharField(blank=True, default="192.168.000.109", max_length=45),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="server_port",
            field=models.PositiveIntegerField(default=7743, validators=[MinValueValidator(1), MaxValueValidator(65535)]),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="server_required",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="attendancedevice",
            name="use_domain_name",
            field=models.BooleanField(default=True),
        ),
    ]
