import os
import csv
from Rachel.models import Country
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Populate the Country model with data from a CSV file'

    def handle(self, *args, **options):
        # Path to the countries.csv file
        csv_file_path = os.path.join(os.path.dirname(__file__), 'countries.csv')

        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Assuming your CSV has these columns: name, region, iso3, phone_code
                    name = row['name']
                    region = row['region']
                    iso3 = row['iso3']
                    phone_code = row['phone_code']

                    # Create or update the country
                    country, created = Country.objects.get_or_create(
                        iso3=iso3,
                        defaults={
                            'name': name,
                            'region': region,
                            'phone_code': phone_code
                        }
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Successfully added country {name}'))
                    else:
                        # Update existing country with new data
                        country.name = name
                        country.region = region
                        country.phone_code = phone_code
                        country.save()
                        self.stdout.write(self.style.SUCCESS(f'Updated country {name}'))

        except FileNotFoundError:
            raise CommandError(f'File {csv_file_path} does not exist')
        except Exception as e:
            raise CommandError(f'Error populating Country model: {e}')
