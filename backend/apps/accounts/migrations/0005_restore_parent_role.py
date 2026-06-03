from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_remove_parent_role"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("super_admin", "Super Admin"),
                    ("admin", "Admin"),
                    ("teacher", "Teacher"),
                    ("student", "Student"),
                    ("parent", "Parent"),
                ],
                default="admin",
                max_length=32,
            ),
        ),
    ]
