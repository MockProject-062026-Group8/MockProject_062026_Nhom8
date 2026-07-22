from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Value
from django.db.models.functions import Concat
from apps.residents.models import Resident
from .list_serializers import ResidentListSerializer

class SC017Pagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100

    def __init__(self):
        super().__init__()
        self.summary_data = {}

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data['summary'] = self.summary_data
        ordered_data = {
            'count': response.data['count'],
            'next': response.data['next'],
            'previous': response.data['previous'],
            'summary': self.summary_data,
            'results': response.data['results']
        }
        response.data = ordered_data
        return response

class ResidentListAPIView(generics.ListAPIView):
    serializer_class = ResidentListSerializer
    pagination_class = SC017Pagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Resident.objects.all()

        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.annotate(
                annotated_full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(resident_id__icontains=search) |
                Q(bed__room__room_number__icontains=search) |
                Q(annotated_full_name__icontains=search)
            )

        referral = self.request.query_params.get('referral_source', '').strip()
        if referral:
            qs = qs.filter(referral_source__iexact=referral)

        total = qs.count()
        active = qs.filter(status=Resident.Status.ACTIVE).count()
        discharged = qs.filter(status=Resident.Status.DISCHARGED).count()
        pending = qs.filter(status=Resident.Status.PENDING).count()

        self.summary_data = {
            "total": total,
            "active": active,
            "discharged": discharged,
            "pending": pending
        }

        status_param = self.request.query_params.get('status', '').strip()
        if status_param:
            valid_statuses = [c[0].upper() for c in Resident.Status.choices]
            status_upper = status_param.upper()
            if status_upper not in valid_statuses:
                raise ValidationError({"status": ["Invalid status value."]})
            qs = qs.filter(status=status_upper)

        ordering = self.request.query_params.get('ordering', '').strip()
        allowed_ordering = [
            'created_at', '-created_at',
            'first_name', '-first_name',
            'last_name', '-last_name',
            'resident_id', '-resident_id'
        ]

        if ordering not in allowed_ordering:
            ordering = '-created_at'

        qs = qs.order_by(ordering)

        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            self.paginator.summary_data = getattr(self, 'summary_data', {})
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
