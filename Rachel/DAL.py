import logging
from django.core.exceptions import ObjectDoesNotExist , ValidationError
from typing import Type, Optional, Tuple, List, Any
from django.db.models import Model, QuerySet
from datetime import timedelta
from django.utils import timezone


logger = logging.getLogger(__name__)

class DAL:



    def get_by_id(self, model: Type[Model], value: Any, field_name: str = 'pk') -> Optional[Model]:
        """
        Retrieve an instance of a model by its ID or other specified field.
        :param model: The model class to retrieve an instance from.
        :param value: The value of the field to filter on.
        :param field_name: The name of the field to filter on. Defaults to primary key.
        :return: An instance of the model or None if not found.
        """
        try:
            return model.objects.get(**{field_name: value})
        except ObjectDoesNotExist:
            logger.error(f"get_by_id - No {model.__name__} found with {field_name}={value}")
            return None
        except Exception as e:
            logger.exception(f"get_by_id - Unexpected Error: {str(e)}")
            return None
            



    def get_all(self, model: Type[Model]) -> QuerySet:
        """
        Retrieve all non-deleted instances of a model.
        :param model: The model class to retrieve non-deleted instances from.
        :return: QuerySet of non-deleted model instances.
        """
        try:
            return model.objects.filter(deleted_at__isnull=True)
        except Exception as e:
            logger.error(f"get_all - Error: {str(e)}")
            return model.objects.none()
        



    def get_or_create(self, model: Type[Model], defaults: Optional[dict] = None, **kwargs) -> Tuple[Optional[Model], bool]:
        """
        Retrieve an instance of a model or create it if it doesn't exist.
        :param model: The model class to retrieve or create an instance.
        :param defaults: A dictionary of default values to use when creating an instance.
        :param kwargs: The conditions to get or create an instance.
        :return: A tuple of (instance, created), where 'created' is a boolean indicating whether the instance was created.
        """
        try:
            instance, created = model.objects.get_or_create(defaults=defaults, **kwargs)
            return instance, created
        except Exception as e:
            logger.error(f"get_or_create - Error: {str(e)}")
            return None, False
        



    def create(self, model: Type[Model], **kwargs) -> Optional[Model]:
        """
        Create an instance of a model with the provided attributes.
        :param model: The model class to create an instance of.
        :param kwargs: The attributes to set on the new instance.
        :return: The newly created model instance or None if creation failed.
        """
        try:
            return model.objects.create(**kwargs)
        except Exception as e:
            logger.error(f"create - Error: {str(e)}")
            return None




    def update(self, instance: Model, **kwargs) -> Optional[Model]:
        """
        Update attributes of a model instance and save it.
        :param instance: The model instance to update.
        :param kwargs: The attributes to update on the instance.
        :return: The updated model instance or None if update failed.
        """
        try:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            instance.save()
            return instance
        except Exception as e:
            logger.error(f"update - Error: {str(e)}")
            return None




    def delete(self, instance: Model) -> bool:
        """
        Soft delete a model instance with timestamp.
        :param instance: The model instance to soft delete.
        :return: True if deletion was successful, False otherwise.
        """
        try:
            instance.deleted_at = timezone.now()
            instance.save()
            return True
        except Exception as e:
            logger.error(f"soft_delete - Error: {str(e)}")
            return False




    def bulk_create(self, model: Type[Model], objects: List[Model]) -> Optional[List[Model]]:
        """
        Bulk create multiple model instances.
        :param model: The model class to create instances of.
        :param objects: A list of model instances to be created.
        :return: The list of created model instances or None if bulk creation failed.
        """
        try:
            return model.objects.bulk_create(objects)
        except Exception as e:
            logger.error(f"bulk_create - Error: {str(e)}")
            return None



    def get_related(self, instance, related_name):

        """
        Retrieve related objects for a given instance.
        :param instance: The instance to retrieve related objects for.
        :param related_name: The name of the related field.
        :return: The related object or None if it does not exist.
        """
       
        try:
            return getattr(instance, related_name)
        except ObjectDoesNotExist:
            logger.error(f"get_related - No related object found for {instance} with related name={related_name}")
            return None
        except Exception as e:
            logger.error(f"get_related - Error: {str(e)}")
            return None

    def filter(self, model, **kwargs):

        """
        Filter objects based on given conditions.
        :param model: The model class to filter objects from.
        :param kwargs: The conditions to filter by.
        :return: QuerySet of filtered objects.
        """
        try:
            return model.objects.filter(**kwargs)
        except Exception as e:
            logger.error(f"filter - Error: {str(e)}")
            return model.objects.none()  # Return an empty QuerySet
        

    def is_locked_out(self, instance) -> bool:
        """
        Check if a user is locked out.
        :param instance: The FailedLoginAttempt instance.
        :return: True if locked out, False otherwise.
        """
        return instance.lockout_until and timezone.now() < instance.lockout_until

    def lock_out(self, instance: Model) -> None:
        """
        Lock out a user for a specified period.
        :param instance: The FailedLoginAttempt instance to lock out.
        """
        try:
            instance.lockout_until = timezone.now() + timedelta(minutes=5)
            instance.save()
        except ValidationError as e:
            logger.warning(f"lock_out - Validation error: {str(e)}")
        except Exception as e:
            logger.exception(f"lock_out - Unexpected error: {str(e)}")
