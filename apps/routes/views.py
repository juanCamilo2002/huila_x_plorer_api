from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Route, RouteStop
from .serializers import RouteSerializer, RouteStopSerializer
from .permissions import IsOwnerOrAdmin

class RouteViewSet(viewsets.ModelViewSet):
    serializer_class = RouteSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            if user.role == 'ADMIN':
                return Route.objects.all()
            return Route.objects.filter(
                Q(is_public=True) | Q(user=user)
            )
        return Route.objects.filter(is_public=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        
        if self.action in ["create"]:
            return [IsAuthenticated()]

        return [IsAuthenticated(), IsOwnerOrAdmin()]
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def clone(self, request, pk=None):
        original: Route = self.get_object()

        is_admin = getattr(request.user, 'role', None) == 'ADMIN' or request.user.is_staff or request.user.is_superuser
        is_owner = original.user_id == request.user.id

        if not (original.is_public or is_owner or is_admin):
            return Response(
                {'detail': 'solo puedes clonar rutas públicas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_name = request.data.get("name") or f"Copia de {original.name}"
        
        with transaction.atomic():
            cloned = Route.objects.create(
                user=request.user,
                name=new_name,
                description=original.description,
                days=original.days,
                is_public=False
            )

            stops = []

            for s in original.stops.order_by("day", "order"):
                stops.append(RouteStop(
                    route=cloned,
                    tourist_spot=s.tourist_spot,
                    day=s.day,
                    order=s.order,
                    notes=s.notes
                ))
            RouteStop.objects.bulk_create(stops)
        serializer = self.get_serializer(cloned)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RouteStopViewSet(viewsets.ModelViewSet):
    serializer_class = RouteStopSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RouteStop.objects.filter(route__user=self.request.user)

    def perform_create(self, serializer):
        route = serializer.validated_data["route"]

        if route.user != self.request.user:
            raise PermissionDenied("No puedes modificar esta ruta.")

        serializer.save()