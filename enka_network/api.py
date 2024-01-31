from utility import config


class EnkaAPI:
    BASE_URL = "https://enka.network"
    USER_URL = BASE_URL + "/u/" + "{uid}"
    USER_DATA_URL = BASE_URL + "/api/uid/{uid}"

    @classmethod
    def get_user_url(cls, uid: int) -> str:
        return cls.USER_URL.format(uid=uid)

    @classmethod
    def get_user_data_url(cls, uid: int) -> str:
        return cls.USER_DATA_URL.format(uid=uid) + (
            f"?key={config.enka_api_key}" if config.enka_api_key else ""
        )


class EnkaError:
    class GeneralError(Exception):
        message: str = "Currently unable to retrieve data from the API server."

        def __str__(self) -> str:
            return self.message

    class Maintenance(GeneralError):
        message = "Currently undergoing maintenance. Enka API server is unavailable."

    class PlayerNotExist(GeneralError):
        message = "UID not found. This player does not exist."

    class RateLimit(GeneralError):
        message = "Currently experiencing rate limits while making requests to Enka API. Please try again later."

    class ServerError(GeneralError):
        message = "Error on Enka API server side. Currently unavailable."

    class WrongUIDFormat(GeneralError):
        message = "Incorrect UID format."
