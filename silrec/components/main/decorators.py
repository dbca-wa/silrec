import functools
import logging
import time
import traceback

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import connection, reset_queries
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import APIException

from silrec import helpers

logger = logging.getLogger(__name__)


def basic_exception_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            raise serializers.ValidationError(e)
        except serializers.ValidationError as e:
            raise e
        except Exception as e:
            logger.exception(e)
            if settings.DEBUG:
                detail = {
                    "user message (settings.API_EXCEPTION_MESSAGE)": settings.API_EXCEPTION_MESSAGE,
                    "type": type(e),
                    "error": str(e),
                    "stacktrace": traceback.format_exc(),
                }
                raise APIException(code=500, detail=detail)
            # Don't send complex exeption messages to the client when in production
            raise APIException(settings.API_EXCEPTION_MESSAGE)

    return wrapper


def user_notexists_exception_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ObjectDoesNotExist:
            logger.error(f"EmailUser {args[0]} does not exist.")
            return None

    return wrapper


def logging_action(**kwargs):
    """Decorator that will log custom actions on viewset

    The model for the viewset must have a log_user_action method
    """

    def decorator(func):
        @action(**kwargs)
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            try:
                result = func(self, request, *args, **kwargs)
                instance = self.get_object()
                logging_method = getattr(instance, "log_user_action", None)
                if not logging_method or not callable(logging_method):
                    raise AttributeError(
                        "Model instance must have a log_user_action method"
                    )
                instance_identifier = helpers.get_instance_identifier(instance)
                model_name = instance._meta.verbose_name.title()
                action_name = func.__name__.replace("_", " ").title()
                instance.log_user_action(
                    f"{model_name}: {instance_identifier} -> {action_name}", request
                )
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise e

        return wrapper

    return decorator


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if "log_time" in kw:
            name = kw.get("log_name", method.__name__.upper())
            kw["log_time"][name] = int((te - ts) * 1000)
        else:
            logger.info(f"{method.__name__!r}  {(te - ts) * 1000:2.2f} ms")
        return result

    return timed


def query_debugger(func):
    @functools.wraps(func)
    def inner_func(*args, **kwargs):
        reset_queries()
        start_queries = len(connection.queries)
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        end_queries = len(connection.queries)
        function_name = f"Function : {func.__name__}"
        number_of_queries = f"Number of Queries : {end_queries - start_queries}"
        time_taken = f"Finished in : {(end - start):.2f}s"
        logger.info(function_name)
        logger.info(number_of_queries)
        logger.info(time_taken)
        return result

    return inner_func
