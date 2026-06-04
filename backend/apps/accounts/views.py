from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.models import AuditAction, AuditEvent
from apps.core.permissions import RoleAccessPermission

from .captcha import generate_captcha_challenge
from .models import User, UserRole
from .serializers import ERPTokenObtainPairSerializer, UserAdminSerializer, UserSerializer

ADMIN_ROLES = (UserRole.SUPER_ADMIN, UserRole.ADMIN)


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
        return response


class CaptchaChallengeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "captcha"

    def get(self, request):
        challenge = generate_captcha_challenge()
        return Response(
            {
                "challenge_id": challenge.challenge_id,
                "code": challenge.code,
                "expires_in": challenge.expires_in,
                "expires_at": challenge.expires_at,
            }
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Log profile update event
        AuditEvent.objects.create(
            actor=request.user,
            action=AuditAction.UPDATE,
            entity_type="User",
            entity_id=str(request.user.pk),
            summary="User updated own profile details",
            ip_address=get_client_ip(request),
        )
        return Response(serializer.data)

    def put(self, request):
        return self.patch(request)


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
        if getattr(self.request.user, "role", None) == UserRole.ADMIN:
            from apps.core.models import CampusMembership

            campus_ids = CampusMembership.objects.filter(user=self.request.user).values_list("campus_id", flat=True)
            return (
                queryset.exclude(role=UserRole.SUPER_ADMIN)
                .filter(campus_memberships__campus_id__in=campus_ids)
                .distinct()
            )
        return queryset

    @action(detail=True, methods=["get"], url_path="detail")
    def detail_view(self, request, pk=None):
        user = self.get_object()
        user_data = self.get_serializer(user).data

        # Get recent audit events where this user was the actor
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
