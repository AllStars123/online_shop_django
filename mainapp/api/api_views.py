from rest_framework.generics import ListAPIView

from .serializers import *
from ..models import *


class CategoryListApiView(ListAPIView):
    serializer_class = CategorySerializer
    queryset = Categories.objects.all()
