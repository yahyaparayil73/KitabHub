from rest_framework.decorators import api_view
from rest_framework.response import Response

from seller.models import Book
from .serializers import BookSerializer


@api_view(["GET"])
def book_list(request):

    books = Book.objects.all()

    serializer = BookSerializer(
        books,
        many=True
    ) 

    return Response(serializer.data)