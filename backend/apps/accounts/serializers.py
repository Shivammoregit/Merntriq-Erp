from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .captcha import validate_captcha_response
from .models import User, UserRole


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    campuses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "campuses",
            "is_active",
        )

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name() or obj.username

    def get_campuses(self, obj: User) -> list[dict]:
        memberships = getattr(obj, "campus_memberships", None)
        if memberships is None:
            return []
        return [
            {
                "id": membership.campus_id,
                "name": membership.campus.name,
                "code": membership.campus.code,
                "logo_url": membership.campus.logo_url,
                "logo_alt_text": membership.campus.logo_alt_text,
                "role": membership.role,
                "is_primary": membership.is_primary,
                "can_manage_users": membership.can_manage_users,
                "can_configure_attendance": membership.can_configure_attendance,
            }
            for membership in memberships.select_related("campus").all()
        ]


class UserAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    full_name = serializers.SerializerMethodField()
    campuses = serializers.SerializerMethodField()
    campus_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "phone_number",
            "campuses",
            "campus_ids",
            "must_change_password",
            "is_active",
            "is_staff",
            "password",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name() or obj.username

    def get_campuses(self, obj: User) -> list[dict]:
        return [
            {
                "id": membership.campus_id,
                "name": membership.campus.name,
                "code": membership.campus.code,
                "logo_url": membership.campus.logo_url,
                "logo_alt_text": membership.campus.logo_alt_text,
                "role": membership.role,
                "is_primary": membership.is_primary,
                "can_manage_users": membership.can_manage_users,
                "can_configure_attendance": membership.can_configure_attendance,
            }
            for membership in obj.campus_memberships.select_related("campus").all()
        ]

    def validate_role(self, value):
        if value == UserRole.SUPER_ADMIN:
            request = self.context.get("request")
            if not request or getattr(request.user, "role", None) != UserRole.SUPER_ADMIN:
                raise serializers.ValidationError("Only a super admin can create or edit super admins.")
        return value

    def validate_campus_ids(self, value):
        request = self.context.get("request")
        if not request or getattr(request.user, "role", None) == UserRole.SUPER_ADMIN:
            return value
        from apps.core.models import CampusMembership

        allowed = set(CampusMembership.objects.filter(user=request.user).values_list("campus_id", flat=True))
        if not set(value).issubset(allowed):
            raise serializers.ValidationError("Admins can assign users only to their own campuses.")
        return value

    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", None))
        campus_ids = attrs.get("campus_ids", None)
        if role != UserRole.SUPER_ADMIN and campus_ids is not None and not campus_ids:
            raise serializers.ValidationError({"campus_ids": "Select at least one campus for this user."})
        if self.instance is None and role != UserRole.SUPER_ADMIN and campus_ids is None:
            raise serializers.ValidationError({"campus_ids": "Select at least one campus for this user."})
        return attrs

    def sync_campus_memberships(self, user: User, campus_ids: list[int] | None) -> None:
        if campus_ids is None:
            return
        from apps.core.models import CampusMemberRole, CampusMembership

        CampusMembership.objects.filter(user=user).delete()
        role_map = {
            UserRole.ADMIN: CampusMemberRole.IT_ADMIN,
            UserRole.TEACHER: CampusMemberRole.TEACHER,
            UserRole.STUDENT: CampusMemberRole.SUPPORT,
            UserRole.PARENT: CampusMemberRole.SUPPORT,
        }
        membership_role = role_map.get(user.role, CampusMemberRole.SUPPORT)
        for index, campus_id in enumerate(dict.fromkeys(campus_ids)):
            CampusMembership.objects.create(
                user=user,
                campus_id=campus_id,
                role=membership_role,
                is_primary=index == 0,
                can_manage_users=user.role == UserRole.ADMIN,
                can_configure_attendance=user.role == UserRole.ADMIN,
            )

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        campus_ids = validated_data.pop("campus_ids", None)
        user = User(**validated_data)
        if user.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
            user.is_staff = True
        else:
            user.is_staff = False
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            user.must_change_password = True
        user.save()
        self.sync_campus_memberships(user, campus_ids)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        campus_ids = validated_data.pop("campus_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if instance.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
            instance.is_staff = True
        else:
            instance.is_staff = False
        if password:
            instance.set_password(password)
            instance.must_change_password = False
        instance.save()
        self.sync_campus_memberships(instance, campus_ids)
        return instance


class ERPTokenObtainPairSerializer(TokenObtainPairSerializer):
    captcha_id = serializers.CharField(write_only=True, required=True)
    captcha_answer = serializers.CharField(write_only=True, required=True, trim_whitespace=True)

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token

    def validate(self, attrs):
        captcha_id = attrs.pop("captcha_id", "")
        captcha_answer = attrs.pop("captcha_answer", "")
        if not validate_captcha_response(captcha_id, captcha_answer):
            raise serializers.ValidationError(
                {"captcha_answer": "Captcha is incorrect or expired. Refresh the captcha and try again."}
            )
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
