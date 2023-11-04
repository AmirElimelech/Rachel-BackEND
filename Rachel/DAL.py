import logging
from django.core.exceptions import ObjectDoesNotExist
from typing import Type, Optional, Tuple, List, Any
from django.db.models import Model, QuerySet



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
            logger.error(f"get_by_id - Error: {str(e)}")
            return None
            



    def get_all(self, model: Type[Model]) -> QuerySet:
        """
        Retrieve all instances of a model.
        :param model: The model class to retrieve instances from.
        :return: QuerySet of model instances.
        """
        try:
            return model.objects.all()
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
        Delete a model instance.
        :param instance: The model instance to delete.
        :return: True if deletion was successful, False otherwise.
        """
        try:
            instance.delete()
            return True
        except Exception as e:
            logger.error(f"delete - Error: {str(e)}")
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