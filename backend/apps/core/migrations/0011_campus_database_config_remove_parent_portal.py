from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_teachersubjectallocation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="campus",
            name="database_alias",
            field=models.CharField(
                blank=True,
                help_text="Optional Django database alias used when this campus is isolated in its own database.",
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name="campus",
            name="database_name",
            field=models.CharField(
                blank=True,
                help_text="Optional physical database name for operator reference.",
                max_length=128,
            ),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="audience",
            field=models.CharField(
                choices=[
                    ("all", "All users"),
                    ("admins", "Admins"),
                    ("staff", "Teachers and staff"),
                    ("learners", "Students"),
                ],
                default="all",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="studentguardian",
            name="relationship",
            field=models.CharField(default="Guardian", max_length=40),
        ),
    ]
