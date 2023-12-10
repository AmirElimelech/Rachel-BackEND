import os
import csv
from django.db import transaction
from Rachel.models import City, Country
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Populate the City model with data from a CSV file'

    def handle(self, *args, **options):
        # Path to the cities.csv file
        csv_file_path = os.path.join(os.path.dirname(__file__), 'cities.csv')

        with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:  # Note the encoding here
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Strip the BOM from the 'city_name' key if present
                city_name_key = next((k for k in row if 'city_name' in k), None)
                if city_name_key is None:
                    raise CommandError("CSV does not contain 'city_name' header")

                city_name = row[city_name_key]
                country_iso3 = row['country_iso3']
                population = int(row['population']) 

                try:
                    # Wrap the operation in a transaction to ensure database integrity
                    with transaction.atomic():
                        # Get the corresponding country object by the ISO code
                        country = Country.objects.get(iso3=country_iso3)

                        # Create a new city object and link it to the country
                        city, created = City.objects.get_or_create(
                            name=city_name,
                            country=country,
                            defaults={'population': population}
                        )

                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Successfully added city {city_name}'))
                        else:
                            # If the city already exists, you may choose to update or ignore
                            self.stdout.write(self.style.WARNING(f'City {city_name} already exists in the database'))

                except Country.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Country with ISO code {country_iso3} does not exist.'))
                except IntegrityError as e:
                    raise CommandError(f'Error adding city {city_name}: {e}')
                except Exception as e:
                    raise CommandError(f'Unexpected error occurred: {e}')
