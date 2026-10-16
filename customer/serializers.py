from rest_framework import serializers
from seller.models import Book

class BookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "price",
            "stock"
        ]