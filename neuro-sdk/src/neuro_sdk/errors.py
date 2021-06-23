class ConfigError(RuntimeError):
    pass


class ClientError(Exception):
    pass


class IllegalArgumentError(ValueError):
    pass


class AuthError(ClientError):
    pass


class AuthenticationError(AuthError):
    pass


class AuthorizationError(AuthError):
    pass


class ResourceNotFound(ValueError):
    pass


class ServerNotAvailable(ValueError):
    pass


class ConfigLoadException(Exception):
    pass


class NDJSONError(ValueError):
    pass
