from decimal import Decimal
from typing import Any, Dict

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Restaurant
from .utils import calculate_restaurant_rating


class DateQueryParamSerializer(serializers.Serializer):
    """
    Serializer to validate the query parameters that we get from the API.

    Basically, this validates that we get datetime in correct format and makes sure date_from greater than date_to.
    """

    date_to = serializers.DateField(format="%Y-%m-%d", required=False)
    date_from = serializers.DateField(format="%Y-%m-%d", required=False)

    def validate(self, data: Dict[str, Any]) -> Dict:
        """
        Validate the date_to and date_from to if both is provided make sure date_from is greater than date_to

        Args:
            data: data to be validated.

        Returns:
            A newly created restaurant instance.
        """
        date_to = data.get("date_to")
        date_from = data.get("date_from")

        if date_to and date_from and date_from < date_to:
            raise ValidationError("date_from must be greater than date_to")

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class RestaurantSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Restaurant
        fields = "__all__"
        extra_fields = ["rating"]

    def create(self, validated_data: Dict[str, Any]) -> Restaurant:
        """
        Create a new restaurant instance with the given validated data.

        Args:
            validated_data: The validated data to create the restaurant instance.

        Returns:
            A newly created restaurant instance.
        """
        user = self.context["request"].user
        return Restaurant.objects.create(
            created_by=user, updated_by=user, **validated_data
        )

    def update(
        self, instance: Restaurant, validated_data: Dict[str, Any]
    ) -> Restaurant:
        """
        Update the given restaurant instance with the provided validated data.

        Args:
            instance: The restaurant instance to update.
            validated_data: The validated data to update the restaurant instance.

        Returns:
            The updated restaurant instance.
        """
        user = self.context["request"].user
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.updated_by = user
        instance.save()
        return instance


class RestaurantRatingSerializer(RestaurantSerializer):
    rating = serializers.SerializerMethodField()

    class Meta(RestaurantSerializer.Meta):
        extra_fields = RestaurantSerializer.Meta.extra_fields + ["rating"]

    def get_rating(self, obj: Restaurant) -> Decimal:
        date_to = self.context.get("date_to")
        date_from = self.context.get("date_from")
        rating = calculate_restaurant_rating(obj, date_to=date_to, date_from=date_from)
        return rating


class RestaurantVoteSerializer(serializers.Serializer):
    restaurant = serializers.PrimaryKeyRelatedField(
        queryset=Restaurant.objects.all(), required=True
    )
