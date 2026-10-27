from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .responses import DEFAULT_SUCCESS_MESSAGE


class StandardPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_page_size(self, request):
        self.page_size = getattr(settings, "API_PAGE_SIZE", 20)
        return super().get_page_size(request)

    def get_paginated_response(self, data):
        return Response(
            {
                "success": True,
                "message": DEFAULT_SUCCESS_MESSAGE,
                "data": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "results": data,
                },
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": True},
                "message": {"type": "string"},
                "data": super().get_paginated_response_schema(schema),
            },
        }
