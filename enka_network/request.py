import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from .api import EnkaAPI, EnkaError


async def fetch_enka_data(
    uid: int, cache_data: Optional[Dict[str, Any]] = None, retry: int = 1
) -> Dict[str, Any]:
    async with aiohttp.request(
        "GET",
        EnkaAPI.get_user_data_url(uid),
        headers={"User-Agent": "KT-Yeh/Genshin-Discord-Bot"},
    ) as resp:
        if resp.status == 200:
            resp_data: Dict[str, Any] = await resp.json()
            resp_data["timestamp"] = int(datetime.now().timestamp())
            raw_data = (
                _combine_cache_data(resp_data, cache_data) if cache_data is not None else resp_data
            )
            return raw_data
        else:
            match resp.status:
                case 400:
                    raise EnkaError.WrongUIDFormat()
                case 404:
                    raise EnkaError.PlayerNotExist()
            if retry > 0:
                await asyncio.sleep(0.5)
                return await fetch_enka_data(uid, cache_data, retry=retry - 1)
            else:
                match resp.status:
                    case 429:
                        raise EnkaError.RateLimit()
                    case 424:
                        raise EnkaError.Maintenance()
                    case 500, 503:
                        raise EnkaError.ServerError()
                    case _:
                        raise EnkaError.GeneralError()


def _combine_cache_data(new_data: Dict[str, Any], cache_data: Dict[str, Any]) -> Dict[str, Any]:

    len_new_showAvatar = len(new_data["playerInfo"].get("showAvatarInfoList", []))
    len_cache_showAvatar = len(cache_data["playerInfo"].get("showAvatarInfoList", []))
    len_new_avatarInfo = len(new_data.get("avatarInfoList", []))
    len_cache_avatarInfo = len(cache_data.get("avatarInfoList", []))
    if len_new_showAvatar + len_cache_showAvatar != len_new_avatarInfo + len_cache_avatarInfo:
        return new_data

    def combine_list(new_list: List[Dict[str, Any]], cache_list: List[Dict[str, Any]]):
        for cache_avatarInfo in cache_list:
            if len(new_list) >= 23:
                break

            for new_avatarInfo in new_list:
                if new_avatarInfo["avatarId"] == cache_avatarInfo["avatarId"]:
                    break
            else:
                new_list.append(cache_avatarInfo)

    if "showAvatarInfoList" in cache_data["playerInfo"]:
        if "showAvatarInfoList" not in new_data["playerInfo"]:
            new_data["playerInfo"]["showAvatarInfoList"] = []
        combine_list(
            new_data["playerInfo"]["showAvatarInfoList"],
            cache_data["playerInfo"]["showAvatarInfoList"],
        )

    if "avatarInfoList" in cache_data:
        if "avatarInfoList" not in new_data:
            new_data["avatarInfoList"] = []
        combine_list(new_data["avatarInfoList"], cache_data["avatarInfoList"])

    return new_data
