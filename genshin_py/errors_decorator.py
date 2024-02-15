import asyncio
import datetime
from typing import Callable

import aiohttp
import genshin
import sentry_sdk

from database import Database, User
from utility import LOG

from .errors import GenshinAPIException, UserDataNotFound


def generalErrorHandler(func: Callable):
    async def wrapper(*args, **kwargs):
        user_id = -1
        for arg in args:
            if isinstance(arg, int) and len(str(arg)) >= 15:
                user_id = arg
                break
        try:
            RETRY_MAX = 3
            for retry in range(RETRY_MAX, -1, -1):
                try:
                    result = await func(*args, **kwargs)

                    user = await Database.select_one(User, User.discord_id.is_(user_id))
                    if user is not None:
                        user.last_used_time = datetime.datetime.now()
                        await Database.insert_or_replace(user)

                    return result
                except (genshin.errors.InternalDatabaseError, aiohttp.ClientOSError) as e:
                    LOG.FuncExceptionLog(user_id, f"{func.__name__} (retry={retry})", e)
                    if retry == 0:
                        raise
                    else:
                        await asyncio.sleep(1.0 + RETRY_MAX - retry)
                        continue
        except genshin.errors.DataNotPublic as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            raise GenshinAPIException(e, "This feature is not enabled. Please enable it from the 'Settings' in the 'Personal Record' on the Hoyolab website or app.")  # noqa
        except genshin.errors.InvalidCookies as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            raise GenshinAPIException(e, "Cookie has expired. Please obtain a new Cookie from Hoyolab.")
        except genshin.errors.RedemptionException as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            raise GenshinAPIException(e, e.original)
        except genshin.errors.GenshinException as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            sentry_sdk.capture_exception(e)
            raise GenshinAPIException(e, e.original)
        except UserDataNotFound as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            raise Exception(str(e))
        except Exception as e:
            LOG.FuncExceptionLog(user_id, func.__name__, e)
            sentry_sdk.capture_exception(e)
            raise

    return wrapper
