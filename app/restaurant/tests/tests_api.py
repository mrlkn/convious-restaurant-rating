import os

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from restaurant.models import Restaurant, Vote


class RestaurantTestCase(APITestCase):
    def setUp(self):
        os.environ["MAX_VOTES_PER_DAY"] = "5"
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")

        self.restaurant1 = Restaurant.objects.create(
            name="Restaurant 1", description="Description 1"
        )
        self.restaurant2 = Restaurant.objects.create(
            name="Restaurant 2", description="Description 2"
        )

    def test_create_restaurant(self):
        url = reverse("restaurant:restaurant-list-create")
        data = {"name": "Restaurant 3", "description": "Description 3"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Restaurant.objects.count(), 3)

    def test_update_restaurant(self):
        url = reverse(
            "restaurant:restaurant-retrieve-update-destroy",
            kwargs={"pk": str(self.restaurant1.uuid)},
        )
        data = {"name": "Restaurant 1 Updated", "description": "Description 1 Updated"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.restaurant1.refresh_from_db()
        self.assertEqual(self.restaurant1.name, "Restaurant 1 Updated")
        self.assertEqual(self.restaurant1.description, "Description 1 Updated")

    def test_delete_restaurant(self):
        url = reverse(
            "restaurant:restaurant-retrieve-update-destroy",
            kwargs={"pk": str(self.restaurant1.uuid)},
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Restaurant.objects.count(), 1)

    def test_vote(self):
        url = reverse("restaurant:vote-create")
        data = {"restaurant": self.restaurant1.uuid}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Vote.objects.count(), 1)

    def test_vote_limit(self):
        os.environ["MAX_VOTES_PER_DAY"] = "5"

        url = reverse("restaurant:vote-create")
        data = {"restaurant": self.restaurant1.uuid}
        for i in range(settings.MAX_VOTES_PER_DAY):
            response = self.client.post(url, data)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Vote.objects.count(), 1)

    def test_restaurant_order_by_rating(self):
        url = reverse("restaurant:order-restaurant-list")
        # Vote for restaurant1 once
        self.client.post(url, {"restaurant": self.restaurant1.uuid})

        # Vote for restaurant2 twice
        self.client.post(url, {"restaurant": self.restaurant2.uuid})
        self.client.post(url, {"restaurant": self.restaurant2.uuid})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_restaurant_order_by_rating_date_range(self):
        url = reverse("restaurant:vote-create")
        # Vote for restaurant1 today
        self.client.post(url, {"restaurant": self.restaurant1.uuid})

        # Vote for restaurant2 yesterday
        yesterday = timezone.now() - timezone.timedelta(days=1)
        vote = Vote.objects.create(user=self.user, restaurant=self.restaurant2)
        vote.date = yesterday.date()
        vote.save()

        url = reverse("restaurant:order-restaurant-list")
        # Test with date_to set to yesterday
        response = self.client.get(url, {"date_to": yesterday.strftime("%Y-%m-%d")})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data.get("results")[0]["uuid"], str(self.restaurant2.uuid)
        )

        # Test with date_from set to today
        response = self.client.get(
            url, {"date_from": timezone.now().strftime("%Y-%m-%d")}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data.get("results")[0]["uuid"], str(self.restaurant1.uuid)
        )

        # Test with both date_to and date_from set to today
        response = self.client.get(
            url,
            {
                "date_to": timezone.now().strftime("%Y-%m-%d"),
                "date_from": timezone.now().strftime("%Y-%m-%d"),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data.get("results")[0]["uuid"], str(self.restaurant1.uuid)
        )

        # Test with both date_to and date_from set to yesterday
        response = self.client.get(
            url,
            {
                "date_to": yesterday.strftime("%Y-%m-%d"),
                "date_from": yesterday.strftime("%Y-%m-%d"),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(
            response.data.get("results")[0]["uuid"], str(self.restaurant2.uuid)
        )

        # Test with no date constraints
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get("results")), 2)
        self.assertEqual(
            response.data.get("results")[0]["uuid"], str(self.restaurant1.uuid)
        )
        self.assertEqual(
            response.data.get("results")[1]["uuid"], str(self.restaurant2.uuid)
        )
