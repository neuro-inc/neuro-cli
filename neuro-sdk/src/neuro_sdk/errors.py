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


class NotSupportedError(NotImplementedError):
    pass


class StdStreamError(Exception):
    def __init__(self, exit_code: int) -> None:
        super().__init__(f"Stream finished with exit code {exit_code}")

        self.exit_code = exit_code
