from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Q

from apps.core.models import AuditAction, AuditEvent, UserActivityLog
from apps.core.permissions import RoleAccessPermission

from .captcha import generate_captcha_challenge
from .models import User, UserRole
from .serializers import ERPTokenObtainPairSerializer, PasswordChangeSerializer, UserAdminSerializer, UserSerializer

ADMIN_ROLES = (UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN)


def get_client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class ERPTokenObtainPairView(TokenObtainPairView):
    serializer_class = ERPTokenObtainPairSerializer
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get("username")
            user = User.objects.filter(username=username).first()
            if user:
                AuditEvent.objects.create(
                    actor=user,
                    action=AuditAction.LOGIN,
                    entity_type="User",
                    entity_id=str(user.pk),
                    summary="User login",
                    ip_address=get_client_ip(request),
                )
                UserActivityLog.objects.create(
                    campus=user.school,
                    user=user,
                    activity_type="login",
                    summary="User login",
                    request_path=request.path,
                    method=request.method,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    metadata={"role": user.role},
                )
        return response


class CaptchaChallengeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "captcha"

    @extend_schema(
        responses=inline_serializer(
            name="CaptchaChallengeResponse",
            fields={
                "challenge_id": serializers.CharField(),
                "question": serializers.CharField(),
                "expires_in": serializers.IntegerField(),
                "expires_at": serializers.DateTimeField(),
            },
        )
    )
    def get(self, request):
        challenge = generate_captcha_challenge()
        return Response(
            {
                "challenge_id": challenge.challenge_id,
                "question": challenge.question,
                "expires_in": challenge.expires_in,
                "expires_at": challenge.expires_at,
            }
        )


class LogoutView(APIView):
    """
    Blacklist the submitted refresh token so it cannot be used to obtain new
    access tokens after the user logs out.  The client is responsible for
    discarding the access token from its own storage.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="LogoutRequest",
            fields={"refresh": serializers.CharField()},
        ),
        responses={200: inline_serializer(
            name="LogoutResponse",
            fields={"detail": serializers.CharField()},
        )},
    )
    def post(self, request):
        refresh_token = request.data.get("refresh", "")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=400)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            # Already blacklisted or malformed — treat as success (idempotent).
            pass
        return Response({"detail": "Logged out successfully."})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        AuditEvent.objects.create(
            actor=request.user,
            action=AuditAction.UPDATE,
            entity_type="User",
            entity_id=str(request.user.pk),
            summary="User updated own profile details",
            ip_address=get_client_ip(request),
        )
        return Response(serializer.data)

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    def put(self, request):
        return self.patch(request)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=PasswordChangeSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditEvent.objects.create(
            actor=request.user,
            action=AuditAction.UPDATE,
            entity_type="User",
            entity_id=str(request.user.pk),
            summary="User changed password",
            ip_address=get_client_ip(request),
        )
        return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = [RoleAccessPermission]
    read_roles = ADMIN_ROLES
    write_roles = ADMIN_ROLES
    filterset_fields = ("role", "is_active")
    search_fields = ("username", "first_name", "last_name", "email", "phone_number", "city", "state")

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request.user, "role", None) == UserRole.SCHOOL_ADMIN:
            from apps.core.models import CampusMembership

            campus_ids = [self.request.user.school_id] if self.request.user.school_id else list(
                CampusMembership.objects.filter(user=self.request.user).values_list("campus_id", flat=True)
            )
            return (
                queryset.exclude(role=UserRole.SUPER_ADMIN)
                .filter(Q(campus_memberships__campus_id__in=campus_ids) | Q(school_id__in=campus_ids))
                .distinct()
            )
        return queryset

    def perform_destroy(self, instance):
        if instance.is_protected_super_admin:
            raise PermissionDenied("Super Admin accounts cannot be deleted.")
        instance.delete()

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.is_protected_super_admin and self.request.user.pk != instance.pk:
            raise PermissionDenied("Super Admin accounts cannot be modified by another user.")
        serializer.save()

    @action(detail=True, methods=["get"], url_path="detail")
    def detail_view(self, request, pk=None):
        user = self.get_object()
        user_data = self.get_serializer(user).data

        recent_events = AuditEvent.objects.filter(actor=user)[:50]
        audit_events = [
            {
                "id": event.id,
                "action": event.action,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "summary": event.summary,
                "ip_address": event.ip_address,
                "created_at": event.created_at,
            }
            for event in recent_events
        ]

        user_data["audit_events"] = audit_events
        return Response(user_data)
