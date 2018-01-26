# -*- coding: utf-8 -*-
# Copyright 2017 Openstack Foundation.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import itertools


class ShadowfiendException(Exception):

    message = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.message % kwargs
            except Exception as e:
                raise e

        super(ShadowfiendException, self).__init__(message)


class ConnectionError(ShadowfiendException):
    """Something went wrong trying to connect to a server"""


class ConsumptionUpdateFailed(ShadowfiendException):
    message = "Consumption update failed"


class Timeout(ShadowfiendException):
    """The request time out"""


class SSLError(ShadowfiendException):
    """The request ssl error"""


class InvalidOutputFormat(ShadowfiendException):
    message = "Invalid output format: %(output_format)s"
    code = 400


class InvalidQuotaParameter(ShadowfiendException):
    message = "Must specify project_id and region_name in request body"
    code = 400


class InvalidDeductParameter(ShadowfiendException):
    message = "Must specify reqId, accountNum, money and extdata.order_id"
    code = 400


class Overlimit(ShadowfiendException):
    code = 423
    message = "%(api)s is called overlimited"


class NotAuthorized(ShadowfiendException):
    message = "Not authorized."
    code = 403


class EmptyCatalog(ShadowfiendException):
    message = "The service catalog is empty."


class AdminRequired(NotAuthorized):
    message = "User does not have admin privileges"


class PolicyNotAuthorized(NotAuthorized):
    message = "Policy doesn't allow %(action)s to be performed."


class OperationNotPermitted(NotAuthorized):
    message = "Operation not permitted."


class MissingRequiredParams(ShadowfiendException):
    message = "Missing required parameters: %(reason)s"
    code = 400


class DBError(ShadowfiendException):
    message = "Error in DB backend: %(reason)s"


class GetExternalBalanceFailed(ShadowfiendException):
    message = "Fail to get external balance of account %(user_id)s"


class Invalid(ShadowfiendException):
    message = "Unacceptable parameters."
    code = 400


class InvalidChargeValue(Invalid):
    message = "The charge value %(value)s is invalid."


class InvalidTransferMoneyValue(Invalid):
    message = "The transfer money value %(value)s is invalid.\
            Should't greater than total balance"


class NoBalanceToTransfer(Invalid):
    message = "The balance value is %(value)s,not enough to transfer"


class InvalidUUID(Invalid):
    message = "Expected a uuid but received %(uuid)s."


class InvalidIdentity(Invalid):
    message = "Expected an uuid or int but received %(identity)s."


class ImageUnacceptable(ShadowfiendException):
    message = "Image %(image_id)s is unacceptable: %(reason)s"


class InstanceStateError(ShadowfiendException):
    message = "The state of the instance %(instance_id)s is %(state)s"


class VolumeStateError(ShadowfiendException):
    message = "The state of the volume %(volume_id)s is %(state)s"


# Cannot be templated as the error syntax varies.
# msg needs to be constructed when raised.
class InvalidParameterValue(Invalid):
    message = "%(err)s"


class OrderRenewError(Invalid):
    message = "%(err)s"


class NotFound(ShadowfiendException):
    message = "Resource could not be found."
    code = 404


class EndpointNotFound(NotFound):
    message = "%(endpoint_type)s endpoint for %(service_type)s not found"
    code = 404


class AccountNotFound(NotFound):
    message = "Account %(user_id)s not found"


class AccountUpdateFailed(ShadowfiendException):
    message = "Account update failed"


class AccountByProjectNotFound(NotFound):
    message = "Account %(project_id)s could not be found"


class AccountCreateFailed(ShadowfiendException):
    message = ("Fail to create account %(user_id)s "
               "for the domain %(domain_id)s")


class AccountGetFailed(ShadowfiendException):
    message = "Fail to get account %(user_id)s"


class AccountChargeFailed(ShadowfiendException):
    message = "Fail to charge %(value)s to account %(user_id)s"


class ProjectNotFound(NotFound):
    message = "Project %(project_id)s could not be found"


class ProjectUpdateFailed(ShadowfiendException):
    message = "Project update failed"


class UserProjectNotFound(NotFound):
    message = ("Relationship between User %(user_id)s and "
               "Project %(project_id)s not found")


class UserProjectUpdateFailed(ShadowfiendException):
    message = "User Project update failed"


class ProjectCreateFailed(ShadowfiendException):
    message = ("Fail to create project %(project_id)s "
               "with project_owner %(user_id)s")


class NotSufficientFund(ShadowfiendException):
    message = ("The balance of the billing owner %(user_id)s of "
               "the project %(project_id)s is not sufficient")
    code = 402


class NotSufficientFrozenBalance(ShadowfiendException):
    message = ("The frozen balance of the billing owner %(user_id)s of "
               "the project %(project_id)s is not sufficient")
    code = 402


class OrderBillsNotFound(NotFound):
    message = "Order %(order_id)s bills could not be found"


class ResourceOrderNotFound(NotFound):
    message = "The order of the resource %(resource_id)s not found"


class OrderNotFound(NotFound):
    message = "Order %(order_id)s not found"


class OrderUpdateFailed(ShadowfiendException):
    message = "Order update failed"


class ProductIdNotFound(NotFound):
    message = "Product %(product_id)s could not be found"


class ProductNameNotFound(NotFound):
    message = "Product %(product_name)s could not be found"


class NoValidHost(NotFound):
    message = "No valid host was found. %(reason)s"


class GlanceConnectionFailed(ShadowfiendException):
    message = ("Connection to glance host %(host)s:%(port)s failed: "
               "%(reason)s")


class ImageNotAuthorized(NotAuthorized):
    message = "Not authorized for image %(image_id)s."


class InvalidImageRef(Invalid):
    message = "Invalid image href %(image_href)s."


class CatalogUnauthorized(ShadowfiendException):
    message = "Unauthorised for keystone service catalog."


class CatalogFailure(ShadowfiendException):
    pass


class CatalogNotFound(ShadowfiendException):
    message = ("Attr %(attr)s with value %(value)s not found in keystone "
               "service catalog.")


class HTTPException(ShadowfiendException):
    message = "Requested version of OpenStack Images API is not available."


class InvalidEndpoint(ShadowfiendException):
    message = "The provided endpoint is invalid"


class CommunicationError(ShadowfiendException):
    message = "Unable to communicate with the server."


class ConfigNotFound(ShadowfiendException):
    message = "Could not find config at %(path)s"


# Copy from keystoneclient.apiclient.exceptions
class HTTPError(Exception):
    """The base exception class for all HTTP exceptions."""

    http_status = 0
    message = "HTTP Error"

    def __init__(self, message=None, details=None,
                 response=None, request_id=None,
                 url=None, method=None, http_status=None,
                 user_id=None, project_id=None, owed=None):
        self.http_status = http_status or self.http_status
        self.message = message or self.message
        self.details = details
        self.request_id = request_id
        self.response = response
        self.url = url
        self.method = method
        self.user_id = user_id
        self.project_id = project_id
        self.owed = owed
        formatted_string = "%(message)s (HTTP %(status)s)" % {
            "message": self.message, "status": self.http_status}
        if request_id:
            formatted_string += " (Request-ID: %s)" % request_id
        super(HTTPError, self).__init__(formatted_string)


class HTTPClientError(HTTPError):
    """Client-side HTTP error.

    Exception for cases in which the client seems to have erred.
    """
    message = "HTTP Client Error"


class HTTPServerError(HTTPError):
    """Server-side HTTP error.

    Exception for cases in which the server is aware that it has
    erred or is incapable of performing the request.
    """
    message = "HTTP Server Error"


class BadRequest(HTTPClientError):
    """HTTP 400 - Bad Request.

    The request cannot be fulfilled due to bad syntax.
    """
    http_status = 400
    message = "Bad Request"


class Unauthorized(HTTPClientError):
    """HTTP 401 - Unauthorized.

    Similar to 403 Forbidden, but specifically for use when authentication
    is required and has failed or has not yet been provided.
    """
    http_status = 401
    message = "Unauthorized"


class AuthorizationFailure(HTTPClientError):
    """HTTP 401 - Unauthorized.

    Similar to 403 Forbidden, but specifically for use when authentication
    is required and has failed or has not yet been provided.
    """
    http_status = 401
    message = "Unauthorized"


class PaymentRequired(HTTPClientError):
    """HTTP 402 - Payment Required.

    Reserved for future use.
    """
    http_status = 402
    message = "Payment Required"


class Forbidden(HTTPClientError):
    """HTTP 403 - Forbidden.

    The request was a valid request, but the server is refusing to respond
    to it.
    """
    http_status = 403
    message = "Forbidden"


class HTTPNotFound(HTTPClientError):
    """HTTP 404 - Not Found.

    The requested resource could not be found but may be available again
    in the future.
    """
    http_status = 404
    message = "Not Found"


class MethodNotAllowed(HTTPClientError):
    """HTTP 405 - Method Not Allowed.

    A request was made of a resource using a request method not supported
    by that resource.
    """
    http_status = 405
    message = "Method Not Allowed"


class NotAcceptable(HTTPClientError):
    """HTTP 406 - Not Acceptable.

    The requested resource is only capable of generating content not
    acceptable according to the Accept headers sent in the request.
    """
    http_status = 406
    message = "Not Acceptable"


class ProxyAuthenticationRequired(HTTPClientError):
    """HTTP 407 - Proxy Authentication Required.

    The client must first authenticate itself with the proxy.
    """
    http_status = 407
    message = "Proxy Authentication Required"


class RequestTimeout(HTTPClientError):
    """HTTP 408 - Request Timeout.

    The server timed out waiting for the request.
    """
    http_status = 408
    message = "Request Timeout"


class Conflict(HTTPClientError):
    """HTTP 409 - Conflict.

    Indicates that the request could not be processed because of conflict
    in the request, such as an edit conflict.
    """
    http_status = 409
    message = "Conflict"


class Gone(HTTPClientError):
    """HTTP 410 - Gone.

    Indicates that the resource requested is no longer available and will
    not be available again.
    """
    http_status = 410
    message = "Gone"


class LengthRequired(HTTPClientError):
    """HTTP 411 - Length Required.

    The request did not specify the length of its content, which is
    required by the requested resource.
    """
    http_status = 411
    message = "Length Required"


class PreconditionFailed(HTTPClientError):
    """HTTP 412 - Precondition Failed.

    The server does not meet one of the preconditions that the requester
    put on the request.
    """
    http_status = 412
    message = "Precondition Failed"


class RequestEntityTooLarge(HTTPClientError):
    """HTTP 413 - Request Entity Too Large.

    The request is larger than the server is willing or able to process.
    """
    http_status = 413
    message = "Request Entity Too Large"

    def __init__(self, *args, **kwargs):
        try:
            self.retry_after = int(kwargs.pop('retry_after'))
        except (KeyError, ValueError):
            self.retry_after = 0

        super(RequestEntityTooLarge, self).__init__(*args, **kwargs)


class RequestUriTooLong(HTTPClientError):
    """HTTP 414 - Request-URI Too Long.

    The URI provided was too long for the server to process.
    """
    http_status = 414
    message = "Request-URI Too Long"


class UnsupportedMediaType(HTTPClientError):
    """HTTP 415 - Unsupported Media Type.

    The request entity has a media type which the server or resource does
    not support.
    """
    http_status = 415
    message = "Unsupported Media Type"


class RequestedRangeNotSatisfiable(HTTPClientError):
    """HTTP 416 - Requested Range Not Satisfiable.

    The client has asked for a portion of the file, but the server cannot
    supply that portion.
    """
    http_status = 416
    message = "Requested Range Not Satisfiable"


class ExpectationFailed(HTTPClientError):
    """HTTP 417 - Expectation Failed.

    The server cannot meet the requirements of the Expect request-header field.
    """
    http_status = 417
    message = "Expectation Failed"


class UnprocessableEntity(HTTPClientError):
    """HTTP 422 - Unprocessable Entity.

    The request was well-formed but was unable to be followed due to semantic
    errors.
    """
    http_status = 422
    message = "Unprocessable Entity"


class InternalServerError(HTTPServerError):
    """HTTP 500 - Internal Server Error.

    A generic error message, given when no more specific message is suitable.
    """
    http_status = 500
    message = "Internal Server Error"


# NotImplemented is a python keyword.
class HTTPNotImplemented(HTTPServerError):
    """HTTP 501 - Not Implemented.

    The server either does not recognize the request method, or it lacks
    the ability to fulfill the request.
    """
    http_status = 501
    message = "Not Implemented"


class BadGateway(HTTPServerError):
    """HTTP 502 - Bad Gateway.

    The server was acting as a gateway or proxy and received an invalid
    response from the upstream server.
    """
    http_status = 502
    message = "Bad Gateway"


class ServiceUnavailable(HTTPServerError):
    """HTTP 503 - Service Unavailable.

    The server is currently unavailable.
    """
    http_status = 503
    message = "Service Unavailable"


class GatewayTimeout(HTTPServerError):
    """HTTP 504 - Gateway Timeout.

    The server was acting as a gateway or proxy and did not receive a timely
    response from the upstream server.
    """
    http_status = 504
    message = "Gateway Timeout"


class HTTPVersionNotSupported(HTTPServerError):
    """HTTP 505 - HTTPVersion Not Supported.

    The server does not support the HTTP protocol version used in the request.
    """
    http_status = 505
    message = "HTTP Version Not Supported"


_code_map = dict(
    (cls.http_status, cls)
    for cls in itertools.chain(HTTPClientError.__subclasses__(),
                               HTTPServerError.__subclasses__()))


def from_response(response, method, url):
    """Returns an instance of :class:`HTTPError` or subclass based on response.

    :param response: instance of `requests.Response` class
    :param method: HTTP method used for request
    :param url: URL used for request
    """
    kwargs = {
        "http_status": response.status_code,
        "response": response,
        "method": method,
        "url": url,
        "request_id": response.headers.get("x-compute-request-id"),
    }
    if "retry-after" in response.headers:
        kwargs["retry_after"] = response.headers["retry-after"]

    content_type = response.headers.get("Content-Type", "")
    if content_type.startswith("application/json"):
        try:
            body = response.json()
        except ValueError:
            pass
        else:
            if hasattr(body, "keys"):
                kwargs["message"] = body.get("message")
                kwargs["details"] = body.get("faultstring")
    elif content_type.startswith("text/"):
        kwargs["details"] = response.text

    try:
        cls = _code_map[response.status_code]
    except KeyError:
        if 500 <= response.status_code < 600:
            cls = HTTPServerError
        elif 400 <= response.status_code < 500:
            cls = HTTPClientError
        else:
            cls = HTTPError
    return cls(**kwargs)
