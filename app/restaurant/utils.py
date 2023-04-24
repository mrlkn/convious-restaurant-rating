from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.utils import timezone

from .models import Restaurant, Vote


def check_has_user_reached_max_vote_limit(user: User) -> bool:
    """
    Checks if user has reached the maximum amount of votes allowed per day.


    Args:
        user (User): The user who is voting.

    Returns:
        True: If user has reached the maximum amount of vote allowed per day.
        False: If user has NOT reached the maximum amount of vote allowed per day.
    """
    today_votes = Vote.objects.filter(user=user, date=timezone.now().date()).first()
    if not today_votes:
        return False
    if today_votes.total_votes >= settings.MAX_VOTES_PER_DAY:
        return True


def calculate_vote_weight(user: User, restaurant: Restaurant) -> Vote:
    """
    Calculate the vote weight for a user's vote on a given restaurant.

    Developers note, currently these weights of votes are hardcoded and can not be changed from outside. In real world
    of course depending on the need it might be wise to consider providing these from outside.

    Args:
        user (User): The user who is voting.
        restaurant (Restaurant): The restaurant that the user is voting for.

    Returns:
        vote (Vote): The updated or newly created Vote instance.
    """
    # Check if the user has already voted for this restaurant today
    vote = Vote.objects.filter(
        user=user, restaurant=restaurant, date=timezone.now().date()
    ).first()

    if vote:
        # If a vote exists, update the total_votes and calculate the new weight
        vote.total_votes += 1
        if vote.total_votes == 2:
            vote.total_weight += Decimal("0.5")
        elif vote.total_votes >= 3:
            vote.total_weight += Decimal("0.25")
        vote.save()
    else:
        # If it's the user's first vote for this restaurant today, create a new vote with weight 1
        vote = Vote.objects.create(
            user=user, restaurant=restaurant, total_votes=1, total_weight=1
        )

    return vote


def calculate_restaurant_rating(
    restaurant: Restaurant, date_to=None, date_from=None
) -> Decimal:
    """
    Calculate the rating of a restaurant for a given date range.

    This function calculates the rating of a restaurant by summing the total_weight
    of votes within the specified date range. It also returns the total number of votes
    and the number of unique voters for the restaurant.

    Args:
        restaurant (Restaurant): The restaurant for which the rating is calculated.
        date_to (Optional[datetime.date]): The end date of the date range for which the rating is calculated.
        date_from (Optional[datetime.date]): The start date of the date range for which the rating is calculated.

    Returns:
        rating (Decimal): The aggregated rating for the restaurant within the specified date range.
    """
    vote_queryset = Vote.objects.filter(restaurant=restaurant)

    if date_from:
        vote_queryset = vote_queryset.filter(date__gte=date_from)

    if date_to:
        vote_queryset = vote_queryset.filter(date__lte=date_to)

    rating = vote_queryset.aggregate(
        total_rating=Sum("total_weight"),
        total_votes=Sum("total_votes"),
        unique_voters=Count("user", distinct=True),
    )

    return rating
