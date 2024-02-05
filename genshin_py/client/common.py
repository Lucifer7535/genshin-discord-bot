import asyncio
from typing import Mapping, Sequence

import genshin
import sentry_sdk

import database
from database import Database, GeetestChallenge, User
from utility import LOG, config, get_app_command_mention

from ..errors import UserDataNotFound
from ..errors_decorator import generalErrorHandler


async def get_client(
    user_id: int,
    *,
    game: genshin.Game = genshin.Game.GENSHIN,
    check_uid=True,
) -> genshin.Client:
    user = await Database.select_one(User, User.discord_id.is_(user_id))
    check, msg = await database.Tool.check_user(user, check_uid=check_uid, game=game)
    if check is False or user is None:
        raise UserDataNotFound(msg)

    client = genshin.Client(lang="en-us")
    match game:
        case genshin.Game.GENSHIN:
            uid = user.uid_genshin or 0
            cookie = user.cookie_genshin or user.cookie_default
            if str(uid)[0] in ["1", "2", "5"]:
                client = genshin.Client(region=genshin.Region.CHINESE, lang="en-us")
        case genshin.Game.HONKAI:
            uid = user.uid_honkai3rd or 0
            cookie = user.cookie_honkai3rd or user.cookie_default
        case genshin.Game.STARRAIL:
            uid = user.uid_starrail or 0
            cookie = user.cookie_starrail or user.cookie_default
            if str(uid)[0] in ["1", "2", "5"]:
                client = genshin.Client(region=genshin.Region.CHINESE, lang="en-us")
        case _:
            uid = 0
            cookie = user.cookie_default

    client.set_cookies(cookie)
    client.default_game = game
    client.uid = uid
    return client


@generalErrorHandler
async def get_game_accounts(
    user_id: int, game: genshin.Game
) -> Sequence[genshin.models.GenshinAccount]:
    client = await get_client(user_id, game=game, check_uid=False)
    accounts = await client.get_game_accounts()
    return [account for account in accounts if account.game == game]


@generalErrorHandler
async def set_cookie(user_id: int, cookie: str, games: Sequence[genshin.Game]) -> str:
    LOG.Info(f"Set cookie for {LOG.User(user_id)}: {cookie}")

    client = genshin.Client(lang="en-us")
    client.set_cookies(cookie)

    try:
        accounts = await client.get_game_accounts()
    except genshin.errors.InvalidCookies:
        client.region = genshin.Region.CHINESE
        accounts = await client.get_game_accounts()
    gs_accounts = [a for a in accounts if a.game == genshin.Game.GENSHIN]
    hk3_accounts = [a for a in accounts if a.game == genshin.Game.HONKAI]
    sr_accounts = [a for a in accounts if a.game == genshin.Game.STARRAIL]

    user = await Database.select_one(User, User.discord_id.is_(user_id))
    if user is None:
        user = User(user_id)

    character_list: list[str] = []  
    user.cookie_default = cookie
    if genshin.Game.GENSHIN in games:
        user.cookie_genshin = cookie
        if len(gs_accounts) == 1:
            user.uid_genshin = gs_accounts[0].uid
        elif len(gs_accounts) > 1:
            character_list.append(f"{len(gs_accounts)} Genshin Impact characters")

    if genshin.Game.HONKAI in games:
        user.cookie_honkai3rd = cookie
        if len(hk3_accounts) == 1:
            user.uid_honkai3rd = hk3_accounts[0].uid
        elif len(hk3_accounts) > 1:
            character_list.append(f"{len(hk3_accounts)} Honkai Impact 3 characters")

    if genshin.Game.STARRAIL in games:
        user.cookie_starrail = cookie
        if len(sr_accounts) == 1:
            user.uid_starrail = sr_accounts[0].uid
        if len(sr_accounts) > 1:
            character_list.append(f"{len(sr_accounts)} Star Rail characters")

    await Database.insert_or_replace(user)
    LOG.Info(f"{LOG.User(user_id)} Cookie set successfully")

    result = "Cookie has been set successfully!"
    if len(character_list) > 0:
        result += (
            f"\nYour account has a total of {'、'.join(character_list)},"
            + f"please use {get_app_command_mention('uid-settings')} to specify the characters you want to save."
        )
    return result


async def claim_daily_reward(
    user_id: int,
    *,
    has_genshin: bool = False,
    has_honkai3rd: bool = False,
    has_starrail: bool = False,
    is_geetest: bool = False,
) -> str:
    
    try:
        client = await get_client(user_id, check_uid=False)
    except Exception as e:
        return str(e)

    try:
        await client.check_in_community()
    except genshin.errors.GenshinException as e:
        if e.retcode != 2001:
            LOG.FuncExceptionLog(user_id, "claimDailyReward: Hoyolab", e)
    except Exception as e:
        LOG.FuncExceptionLog(user_id, "claimDailyReward: Hoyolab", e)

    if any([has_genshin, has_honkai3rd, has_starrail]) is False:
        return "No game sign-in selected"

    gt_challenge: GeetestChallenge | None = None
    if not is_geetest:
        gt_challenge = await Database.select_one(
            GeetestChallenge, GeetestChallenge.discord_id.is_(user_id)
        )

    result = ""
    if has_genshin:
        challenge = gt_challenge.genshin if gt_challenge else None
        client = await get_client(user_id, game=genshin.Game.GENSHIN, check_uid=False)
        result += await _claim_reward(user_id, client, genshin.Game.GENSHIN, is_geetest, challenge)
    if has_honkai3rd:
        challenge = gt_challenge.honkai3rd if gt_challenge else None
        client = await get_client(user_id, game=genshin.Game.HONKAI, check_uid=False)
        result += await _claim_reward(user_id, client, genshin.Game.HONKAI, is_geetest, challenge)
    if has_starrail:
        challenge = gt_challenge.starrail if gt_challenge else None
        client = await get_client(user_id, game=genshin.Game.STARRAIL, check_uid=False)
        result += await _claim_reward(
            user_id, client, genshin.Game.STARRAIL, is_geetest, challenge
        )

    return result


async def _claim_reward(
    user_id: int,
    client: genshin.Client,
    game: genshin.Game,
    is_geetest: bool = False,
    gt_challenge: Mapping[str, str] | None = None,
    retry: int = 5,
) -> str:
    game_name = {
        genshin.Game.GENSHIN: "Genshin Impact",
        genshin.Game.HONKAI: "Honkai Impact 3",
        genshin.Game.STARRAIL: "Star Rail",
    }

    try:
        reward = await client.claim_daily_reward(game=game, challenge=gt_challenge)
    except genshin.errors.AlreadyClaimed:
        return f"{game_name[game]} daily rewards have already been claimed today!"
    except genshin.errors.InvalidCookies:
        return "Cookie has expired. Please obtain a new Cookie from Hoyolab."
    except genshin.errors.GeetestTriggered as exception:
        if is_geetest is True and config.geetest_solver_url is not None:
            url = config.geetest_solver_url
            url += f"/geetest/{game}/{user_id}/{exception.gt}/{exception.challenge}"
            return f"Please unlock the captcha on the website: [Click here to open the link]({url})\nIf an error occurs, please use this command again to regenerate the link."
        
        if config.geetest_solver_url is not None:
            command_str = get_app_command_mention("daily-checkin")
            return f"{game_name[game]} sign-in failed: Blocked by captcha. Please use the {command_str} command to choose 'Set Captcha'."
        link: str = {
            genshin.Game.GENSHIN: "https://act.hoyolab.com/ys/event/signin-sea-v3/index.html?act_id=e202102251931481",
            genshin.Game.HONKAI: "https://act.hoyolab.com/bbs/event/signin-bh3/index.html?act_id=e202110291205111",
            genshin.Game.STARRAIL: "https://act.hoyolab.com/bbs/event/signin/hkrpg/index.html?act_id=e202303301540311",
        }.get(game, "")
        return f"{game_name[game]} sign-in failed: Blocked by captcha. Please manually sign in on the [official website]({link})."
    except Exception as e:
        if isinstance(e, genshin.errors.GenshinException) and e.retcode == -10002:
            return f"{game_name[game]} sign-in failed. No character data found for the currently logged-in account."
        if isinstance(e, genshin.errors.GenshinException) and e.retcode == 50000:
            return f"{game_name[game]} request failed. Please try again later."

        LOG.FuncExceptionLog(user_id, "claimDailyReward", e)
        if retry > 0:
            await asyncio.sleep(1)
            return await _claim_reward(user_id, client, game, is_geetest, gt_challenge, retry - 1)

        LOG.Error(f"{LOG.User(user_id)} {game_name[game]} sign-in failed")
        sentry_sdk.capture_exception(e)
        return f"{game_name[game]} sign-in failed: {e}."
    else:
        return f"{game_name[game]} sign-in successful today! Received {reward.amount}x {reward.name}!"