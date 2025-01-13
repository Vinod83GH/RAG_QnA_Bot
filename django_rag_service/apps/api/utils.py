import copy
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


"""
The following define standard formats for the responses.

Usage:
    from apps.api.utils import format_response
    if 'error' in request.query_params:
        # The business error condition
        data = {
            'internal_message': "Handle something",
            'external_message': "Oops! Something went wrong. Try again later"
        }
        response_data = format_response("ERROR_RESPONSE", data, 400)
    else:
        response_data = format_response("SUCCESS_RESPONSE", serializer.data, status.HTTP_200_OK)
    return Response(response_data)
"""


BUSINESS_ERROR_CODE = 'business'

SUCCESS_RESPONSE = {
    'status_code': None,
    'data': None
}

ERROR_RESPONSE = {
    'status_code': None,
    'error': {
        'internal_message': None,
        'external_message': None,
    }
}


def format_response(reponse_type, data, status_code):
    if reponse_type == 'SUCCESS_RESPONSE':
        response_data = copy.deepcopy(SUCCESS_RESPONSE)
        response_data['status_code'] = status_code
        response_data['data'] = data
    elif reponse_type == 'ERROR_RESPONSE':
        response_data = copy.deepcopy(ERROR_RESPONSE)
        response_data['status_code'] = status_code
        response_data['error'] = data
    else:
        response_data = {}
    return response_data


def is_business_error(error):
    """Recursively checks for business errors."""
    if isinstance(error, dict):
        for field, codes in error.items():
            if is_business_error(codes):
                return True
    elif isinstance(error, list):
        for item in error:
            if is_business_error(item):
                return True
    elif isinstance(error, str) and error == BUSINESS_ERROR_CODE:
        return True
    return False


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.

    business_error = False
    # check if the exception occured because of business validations
    if isinstance(exc, APIException) and type(exc.get_codes()) == dict:

        # Business errors are thrown as dictionaries
        # DRF conditionally changes the type of the error codes, so this check is a must
        business_error = is_business_error(exc.get_codes())

    if business_error:
        # Business validations failed
        data = {
            'internal_message': exc.detail,
            'external_message': "Oops! Something went wrong. Try again later"
        }
        response_data = format_response("ERROR_RESPONSE", data, status.HTTP_400_BAD_REQUEST)
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        response = exception_handler(exc, context)

    return response
