from django.core.management.base import BaseCommand
from account.models import Hobbies

HOBBIES_DATA = [
    "R&B",
    "Gardening",
    "LGBTQ & Rights",
    "Vegetarian",
    "Dancing",
    "Dogs",
    "Museums & galleries",
    "Wine",
    "Writing",
    "Yoga",
    "Baking",
]

class Command(BaseCommand):
    help = "Load default hobbies into the database (without icons)"

    def handle(self, *args, **options):
        for hobby_name in HOBBIES_DATA:
            if Hobbies.objects.filter(hobby=hobby_name).exists():
                self.stdout.write(self.style.WARNING(f"{hobby_name} already exists. Skipping."))
                continue

            hobby_obj = Hobbies.objects.create(hobby=hobby_name)
            self.stdout.write(self.style.SUCCESS(f"Created hobby: {hobby_name}"))
