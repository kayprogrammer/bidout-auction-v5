from ninja.responses import Response
from http import HTTPStatus


class RequestError(Exception):
    default_detail = "An error occured"

    def __init__(self, err_msg: str, status_code: int = 400, data: dict = None) -> None:
        self.status_code = HTTPStatus(status_code)
        self.err_msg = err_msg
        self.data = data

        super().__init__()


def validation_errors(exc):
    # Get the original 'detail' list of errors
    details = exc.errors
    modified_details = {}
    for error in details:
        try:
            field_name = error["loc"][1]
        except:
            field_name = error["loc"][0]

        modified_details[f"{field_name}"] = error["msg"]

    return Response(
        {"status": "failure", "message": "Invalid Entry", "data": modified_details},
        status=422,
    )


def request_errors(exc):
    err_dict = {
        "status": "failure",
        "message": exc.err_msg,
    }
    if exc.data:
        err_dict["data"] = exc.data
    return Response(err_dict, status=exc.status_code)


# def custom_exception_handler(exc, context):
#     try:
#         response = exception_handler(exc, context)
#         if isinstance(exc, AuthenticationFailed):
#             exc_list = str(exc).split("DETAIL: ")
#             return CustomResponse.error(message=exc_list[-1], status_code=401)
#         elif isinstance(exc, RequestError):
#             return CustomResponse.error(
#                 message=exc.err_msg, data=exc.data, status_code=exc.status_code
#             )
#         elif isinstance(exc, ValidationError):
#             errors = exc.detail
#             for key in errors:
#                 errors[key] = str(errors[key][0])
#             return CustomResponse.error(
#                 message="Invalid Entry", data=errors, status_code=422
#             )
#         else:
#             return CustomResponse.error(
#                 message=exc.detail if hasattr(exc, "detail") else exc,
#                 status=response.status_code,
#             )
#     except:
#         print(exc)
#         return CustomResponse.error(message="Server Error", status_code=500)
