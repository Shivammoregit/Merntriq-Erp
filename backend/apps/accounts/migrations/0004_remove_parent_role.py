from django.db import migrations, models


def deactivate_parent_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="parent").update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_user_role"),
    ]

    operations = [
        migrations.RunPython(deactivate_parent_users, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("super_admin", "Super Admin"),
                    ("admin", "Admin"),
                    ("teacher", "Teacher"),
                    ("student", "Student"),
                ],
                default="admin",
                max_length=32,
            ),
        ),
    ]
