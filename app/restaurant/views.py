from django.db.models import Count, Sum
from rest_framework import status, viewsets
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Restaurant, Vote
from .pagination import RestaurantPagination
from .serializers import (
    DateQueryParamSerializer,
    RestaurantRatingSerializer,
    RestaurantSerializer,
    RestaurantVoteSerializer,
)
from .utils import calculate_vote_weight, check_has_user_reached_max_vote_limit


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        TokenAuthentication,
    ]
    permission_classes = [IsAuthenticated]
    pagination_class = RestaurantPagination

    def order_by_ratings(self, request: Request, *args, **kwargs) -> Response:
        """
        Order restaurants by their ratings with a date range if specified.

        This view orders the restaurants based on their aggregated ratings within a
        date range if specified. The rating is calculated by summing the total_weight of
        votes within the date range. Restaurants are ordered by descending rating and
        number of distinct voters.

        Args:
            request (Request): The request object that may contain query parameters for the date range.

        Returns:
            Response: (Response) Paginated & ordered list of restaurants with their ratings and additional information.
        """
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        query_param_serializer = DateQueryParamSerializer(data=request.query_params)
        query_param_serializer.is_valid(raise_exception=True)

        vote_queryset = Vote.objects.all()

        if date_from:
            date_from = query_param_serializer.validated_data.get("date_from")
            vote_queryset = vote_queryset.filter(date__gte=date_from)

        if date_to:
            date_to = query_param_serializer.validated_data.get("date_to")
            vote_queryset = vote_queryset.filter(date__lte=date_to)

        restaurant_queryset = (
            Restaurant.objects.filter(vote__in=vote_queryset)
            .annotate(
                rating=Sum("vote__total_weight"),
                distinct_voters=Count("vote__user", distinct=True),
            )
            .order_by("-rating", "-distinct_voters")
        )

        page = self.paginate_queryset(restaurant_queryset)
        if page is not None:
            serializer = RestaurantRatingSerializer(
                page,
                many=True,
                context={"date_from": date_from, "date_to": date_to},
            )
            return self.get_paginated_response(serializer.data)

        serializer = RestaurantRatingSerializer(
            restaurant_queryset,
            many=True,
            context={"date_from": date_from, "date_to": date_to},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class VoteViewSet(viewsets.GenericViewSet):
    serializer_class = RestaurantVoteSerializer
    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        TokenAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Create or update a vote for a restaurant.

        Args:
            request (Request): The request object containing and restaurant data.

        Returns:
            response (Response): The response depending on different statuses.
        """
        user = request.user
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        restaurant = serializer.validated_data.get("restaurant")

        # Check if the user has reached the max votes per day limit
        limit_has_reached = check_has_user_reached_max_vote_limit(user)
        if limit_has_reached:
            return Response(
                "You have reached your daily voting limit.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate the vote weight and create/update the vote instance
        vote = calculate_vote_weight(user, restaurant)
        if not vote:
            return Response(
                "Internal server error.", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response("User has successfully voted.", status=status.HTTP_200_OK)
