import os
import csv
from Rachel.models import Language
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError



class Command(BaseCommand):
    help = 'Populate the Language model with data from a CSV file'

    def handle(self, *args, **options):
        # Assuming 'populate_languages.py' and 'languages.csv' are in the same directory
        csv_file_path = os.path.join(os.path.dirname(__file__), 'languages.csv')

        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    lang_code = row['lang_code']
                    name = row['name']

                    # Check if language already exists
                    if not Language.objects.filter(lang_code=lang_code).exists():
                        try:
                            language = Language(name=name, lang_code=lang_code)
                            language.full_clean()  # This will check for max_length and other validators
                            language.save()
                            self.stdout.write(self.style.SUCCESS(f'Successfully added language {name}'))
                        except ValidationError as e:
                            self.stdout.write(self.style.WARNING(f'Error adding language {name}: {e}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Language {name} already exists'))
        except FileNotFoundError:
            raise CommandError(f'File {csv_file_path} does not exist')
        except Exception as e:
            raise CommandError(f'Error populating Language model: {e}')