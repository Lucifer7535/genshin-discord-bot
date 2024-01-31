import genshin


class UserDataNotFound(Exception):

    pass


class GenshinAPIException(Exception):

    origin: genshin.GenshinException
    message: str = ""

    def __init__(self, exception: genshin.GenshinException, message: str) -> None:
        self.origin = exception
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.message}\n```{repr(self.origin)}```"
