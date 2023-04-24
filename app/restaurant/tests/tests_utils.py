import os
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from convious import settings
from restaurant.models import Restaurant, Vote
from restaurant.utils import (
    check_has_user_reached_max_vote_limit,
    calculate_vote_weight,
    calculate_restaurant_rating,
)
from django.contrib.auth.models import User


class UtilityTests(TestCase):
    def setUp(self):
        os.environ["MAX_VOTES_PER_DAY"] = "5"
        self.user1 = User.objects.create_user(username="user1", password="password")
        self.user2 = User.objects.create_user(username="user2", password="password")
        self.restaurant1 = Restaurant.objects.create(name="Restaurant 1")
        self.restaurant2 = Restaurant.objects.create(name="Restaurant 2")

    def test_check_has_user_reached_max_vote_limit(self):
        # Test when there's no vote yet
        self.assertFalse(check_has_user_reached_max_vote_limit(self.user1))

        os.environ["MAX_VOTES_PER_DAY"] = "5"

        # Test when the user has reached the max vote limit
        Vote.objects.create(
            user=self.user1,
            restaurant=self.restaurant1,
            total_votes=settings.MAX_VOTES_PER_DAY,
            total_weight=3.75,
        )
        self.assertTrue(check_has_user_reached_max_vote_limit(self.user1))

        # Test when the user has NOT reached the max vote limit
        Vote.objects.create(
            user=self.user2,
            restaurant=self.restaurant1,
            total_votes=2,
            total_weight=1.5,
        )
        self.assertFalse(check_has_user_reached_max_vote_limit(self.user2))

    def test_calculate_vote_weight(self):
        # Test for the first vote
        vote1 = calculate_vote_weight(self.user1, self.restaurant1)
        self.assertEqual(vote1.total_votes, 1)
        self.assertEqual(vote1.total_weight, Decimal("1"))

        # Test for the second vote
        vote2 = calculate_vote_weight(self.user1, self.restaurant1)
        self.assertEqual(vote2.total_votes, 2)
        self.assertEqual(vote2.total_weight, Decimal("1.5"))

        # Test for the third vote
        vote3 = calculate_vote_weight(self.user1, self.restaurant1)
        self.assertEqual(vote3.total_votes, 3)
        self.assertEqual(vote3.total_weight, Decimal("1.75"))

    def test_calculate_restaurant_rating(self):
        # Create some votes
        Vote.objects.create(
            user=self.user1,
            restaurant=self.restaurant1,
            total_votes=2,
            total_weight=1.5,
            date=timezone.now().date(),
        )
        Vote.objects.create(
            user=self.user2,
            restaurant=self.restaurant1,
            total_votes=3,
            total_weight=1.75,
            date=timezone.now().date(),
        )

        # Test without date range
        rating1 = calculate_restaurant_rating(self.restaurant1)
        self.assertEqual(rating1["total_rating"], Decimal("3.25"))
        self.assertEqual(rating1["total_votes"], 5)
        self.assertEqual(rating1["unique_voters"], 2)

        # Test with date range
        date_from = timezone.now().date()
        date_to = timezone.now().date()
        rating2 = calculate_restaurant_rating(self.restaurant1, date_to, date_from)
        self.assertEqual(rating2["total_rating"], Decimal("3.25"))
        self.assertEqual(rating2["total_votes"], 5)
        self.assertEqual(rating2["unique_voters"], 2)
