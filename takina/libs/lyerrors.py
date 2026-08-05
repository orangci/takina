from discord.ext import commands


class TakinaError(commands.CommandError):
    """Base class for all Takina errors."""

    error_name = "Error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class TakinaUserInputError(TakinaError):
    error_name = "User Input Error"


class TakinaPermissionError(TakinaError):
    error_name = "Missing Permissions"


class TakinaBotPermissionError(TakinaError):
    error_name = "Bot Missing Permissions"


class TakinaNotFoundError(TakinaError):
    error_name = "Not Found"


class TakinaDisabledError(TakinaError):
    error_name = "Disabled Command"


class TakinaMaintainerOnlyError(TakinaError):
    error_name = "Maintainer Only Command"
