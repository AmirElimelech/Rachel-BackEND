import logging
from django.utils import timezone
from django.db.models import Model, QuerySet
from typing import  Type,  Optional,  List,  Any
from django.core.exceptions import ObjectDoesNotExist 





logger = logging.getLogger(__name__)

class DAL:



    def get_by_id(self, model: Type[Model], value: Any, field_name: str = 'pk') -> Optional[Model]:

        """
        Retrieve an instance of a model by its ID or other specified field. This method logs the initiation of the retrieval 
        operation and reports the outcome, helping in tracking its usage and diagnosing issues in case of failures.

        :param model: The model class to retrieve an instance from.
        :param value: The value of the field to filter on.
        :param field_name: The name of the field to filter on. Defaults to primary key.
        :return: An instance of the model or None if not found.
        """

        try:
            # Log the start of the retrieval operation
            logger.info(f"Starting get_by_id operation for {model.__name__} with {field_name}={value}")

            instance = model.objects.get(**{field_name: value})

            # Log successful retrieval
            logger.info(f"Successfully retrieved {model.__name__} with {field_name}={value}")

            return instance
        except ObjectDoesNotExist:
            # Log the case where no object is found
            logger.error(f"get_by_id - No {model.__name__} found with {field_name}={value}")
            return None
        except Exception as e:
            # Log any unexpected exceptions
            logger.exception(f"get_by_id - Unexpected Error retrieving {model.__name__} with {field_name}={value}: {str(e)}")
            return None




    def get_all(self, model: Type[Model]) -> QuerySet:

        """
        Retrieve all non-deleted instances of a model.

        This method is enhanced with logging to track its execution. 
        It logs the initiation of the retrieval operation and the number 
        of records found, providing visibility into the process and aiding 
        in troubleshooting if any issues arise.

        :param model: The model class to retrieve non-deleted instances from.
        :return: QuerySet of non-deleted model instances.
        """

        try:
            # Log the start of the retrieval operation
            logger.info(f"Starting get_all operation for {model.__name__}")

            result = model.objects.filter(deleted_at__isnull=True)

            # Log the successful retrieval of records
            logger.info(f"get_all operation completed for {model.__name__}. Number of records found: {len(result)}")

            return result
        except Exception as e:
            # Log any error encountered during retrieval
            logger.error(f"get_all - Error during retrieval for {model.__name__}: {str(e)}")
            return model.objects.none()

        

        

    def get_or_create(self, model, defaults=None, **kwargs):

        """
        Retrieve an existing instance of a model or create it if it does not exist.
        This method first tries to retrieve a model instance based on the provided criteria.
        If an instance is found, it is returned. Otherwise, a new instance is created with the given defaults.

        :param model: The model class to operate on.
        :param defaults: A dictionary of attributes to set on the model instance if it needs to be created.
        :param kwargs: The attributes to filter by when retrieving the model instance.
        :return: A tuple (instance, created), where 'instance' is the retrieved or created model instance, and 'created' is a boolean indicating whether a new instance was created.
        """

        try:
            # Log the start of the get_or_create operation
            logger.info(f"Starting get_or_create operation for {model.__name__} with criteria {kwargs} and defaults {defaults}")

            instance, created = model.objects.get_or_create(defaults=defaults, **kwargs)

            # Log the outcome of the operation
            if created:
                logger.info(f"Created a new instance of {model.__name__}")
            else:
                logger.info(f"Found an existing instance of {model.__name__}")

            return instance, created
        except Exception as e:
            # Log any other exceptions
            logger.error(f"get_or_create - Error during operation on {model.__name__}: {str(e)}")
            return None, False






    def create(self, model: Type[Model], **kwargs) -> Optional[Model]:

        """
        Create an instance of a model with the provided attributes.
        :param model: The model class to create an instance of.
        :param kwargs: The attributes to set on the new instance.
        :return: The newly created model instance or None if creation failed.
        """

        try:
            # Log the start of the creation operation
            logger.info(f"Starting creation operation for a new instance of {model.__name__} with attributes {kwargs}")

            new_instance = model.objects.create(**kwargs)

            # Log the successful creation of the instance
            logger.info(f"Successfully created a new instance of {model.__name__}")

            return new_instance
        except Exception as e:
            # Log the error encountered during creation
            logger.error(f"create - Error during creation of {model.__name__}: {str(e)}")
            return None





    def update(self, instance: Model, **kwargs) -> Optional[Model]:

        """
        Update attributes of a model instance and save it.
        :param instance: The model instance to update.
        :param kwargs: The attributes to update on the instance.
        :return: The updated model instance or None if update failed.
        """

        try:
            # Log the start of the update operation
            logger.info(f"Starting update operation for instance of {instance.__class__.__name__} with attributes {kwargs}")

            for key, value in kwargs.items():
                setattr(instance, key, value)
            instance.save()

            # Log the successful completion of the update
            logger.info(f"Successfully updated instance of {instance.__class__.__name__} with new attributes")

            return instance
        except Exception as e:
            # Log the error
            logger.error(f"update - Error during update of {instance.__class__.__name__}: {str(e)}")
            return None





    def delete(self, instance: Model) -> bool:

        """
        Soft delete a model instance with timestamp.
        :param instance: The model instance to soft delete.
        :return: True if deletion was successful, False otherwise.
        """

        try:
            # Log the start of the soft deletion operation
            logger.info(f"Starting soft delete operation for instance of {instance.__class__.__name__}")

            instance.deleted_at = timezone.now()
            instance.save()

            # Log the successful soft deletion
            logger.info(f"Successfully soft deleted instance of {instance.__class__.__name__}")

            return True
        except Exception as e:
            # Log the error in soft deletion
            logger.error(f"soft_delete - Error during soft deletion of {instance.__class__.__name__}: {str(e)}")
            return False




    def bulk_create(self, model: Type[Model], objects: List[Model]) -> Optional[List[Model]]:

        """
        Bulk create multiple model instances.
        :param model: The model class to create instances of.
        :param objects: A list of model instances to be created.
        :return: The list of created model instances or None if bulk creation failed.
        """

        try:
            # Log the start of the bulk creation operation
            logger.info(f"Starting bulk creation for {len(objects)} instances of {model.__name__}")

            created_objects = model.objects.bulk_create(objects)

            # Log the successful completion of the bulk creation
            logger.info(f"Successfully completed bulk creation. Number of records created: {len(created_objects)}")

            return created_objects
        except Exception as e:
            # Log the error
            logger.error(f"bulk_create - Error during bulk creation for {model.__name__}: {str(e)}")
            return None



    def get_related(self, instance, related_name):
        """
        Retrieve related objects for a given instance.
        :param instance: The instance to retrieve related objects for.
        :param related_name: The name of the related field.
        :return: The related object or None if it does not exist.
        """
        try:
            # Log the start of the operation
            logger.info(f"Starting get_related operation on {instance.__class__.__name__} for related field: {related_name}")

            related_obj = getattr(instance, related_name)

            # Log successful retrieval
            if related_obj is not None:
                logger.info(f"Successfully retrieved related field '{related_name}' for instance {instance.__class__.__name__}")
            else:
                logger.info(f"No related field '{related_name}' found for instance {instance.__class__.__name__}")

            return related_obj
        except ObjectDoesNotExist:
            # Log the case where no related object is found
            logger.error(f"get_related - No related object found for {instance.__class__.__name__} with related name={related_name}")
            return None
        except Exception as e:
            # Log any other exceptions
            logger.error(f"get_related - Error retrieving related field '{related_name}' for instance {instance.__class__.__name__}: {str(e)}")
            return None



    def filter(self, model, **kwargs):

        """
        Filter objects based on given conditions.
        :param model: The model class to filter objects from.
        :param kwargs: The conditions to filter by.
        :return: QuerySet of filtered objects.
        """
        try:
            # Log the start of the filtering operation
            logger.info(f"Starting filter operation on {model.__name__} with conditions: {kwargs}")

            result = model.objects.filter(**kwargs)

            # Log the successful completion of the filtering
            logger.info(f"Filter operation completed on {model.__name__}. Number of records found: {len(result)}")

            return result
        except Exception as e:
            # Log the error
            logger.error(f"filter - Error on filtering {model.__name__} with conditions {kwargs}: {str(e)}")
            return model.objects.none()  # Return an empty QuerySet
            
