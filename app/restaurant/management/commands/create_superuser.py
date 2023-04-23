from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Create a superuser with a default email and password"

    def handle(self, *args, **options):
        # Define the default email and password
        email = "admin@convious.com"
        password = "superultrastrongpassword"
        username = "admin"

        # Check if a user with this email already exists
        if not User.objects.filter(email=email).exists():
            # Create the superuser
            user = User.objects.create_superuser(email=email, password=password, username=username)
            token = Token.objects.create(key="a7259cd9a5ed2bcfa8a958b7efab5151f6185987", user=user)
            self.stdout.write(self.style.SUCCESS(f"Superuser created with email: {email}, token: {token.key}"))
        else:
            self.stdout.write(self.style.WARNING(f"A user with email {email} already exists"))
