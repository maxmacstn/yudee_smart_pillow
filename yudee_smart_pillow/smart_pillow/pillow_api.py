from aiohttp import ClientSession, web
import asyncio
import time
import hashlib
import datetime
import json
import logging

_LOGGER = logging.getLogger(__name__)

STATE_DEEP_SLEEP = 1
STATE_LIGHT_SLEEP = 2
STATE_REM_SLEEP = 3
STATE_AWAKE = 4



class PillowCloudAPI:

    def __init__(self, session: ClientSession, cname: str, cnameType: str, uid: str, mac: str, sort: str) -> None:
        self._session = session
        self._cname = cname
        self._cname_type = cnameType
        self._uid = uid
        self._did = mac.replace(":", "")
        self._sort = sort
        self._token = ""
        self._last_get_token = None
        self._day_report = {}

    def timestamp(self):
        return str(int(time.time()))

    def calculate_md5(self, timestamp) -> str:

        toHash = self._cname + self._did + self._uid + self._sort + timestamp + self._cname_type
        result = hashlib.md5(toHash.encode())

        return result.hexdigest()

    async def get_token(self):
        _LOGGER.debug("Get token")
        timestamp = self.timestamp()
        md5_hash = self.calculate_md5(timestamp)
        url = "http://beacon5c.mirahome.net/beacon5/client/fastlogin"
        body = {"cname": self._cname, "tmsp": timestamp, "sign": md5_hash, "did": self._did, "uid": self._uid}

        async with self._session.post(
            url, raise_for_status=True, json=body
        ) as resp:
            resp_json = await resp.json()
            if resp_json["code"] != "1000":
                raise web.HTTPUnauthorized(
                    reason=f"error code {resp_json['code']}"
                )
            # print(resp_json)
            # self._token = resp_json["data"]
            # self._last_get_token = datetime.datetime.now()
            return resp_json["data"]

    def set_token(self, token:str):
        self._token = token

    def get_status_sleep_time(self, state:int):
        occured_time = ""
        prev_end = ""

        if self._day_report is None:
            return "-"

        for data in self._day_report['sleep_data']:
            

            if data["status"] == state:

                if len(occured_time) > 240:
                    break
  
                start = datetime.datetime.fromtimestamp(data["start"]).strftime("%-H:%M")
                end = datetime.datetime.fromtimestamp(data["end"]).strftime("%-H:%M")
                if (start == prev_end):
                    occured_time.replace(prev_end,end)
                    continue
                else:
                    if occured_time != "":
                        occured_time += " | "
                    occured_time += f"{start}-{end}"

                prev_end = end


        
        if occured_time == "":
            return "-"

        return occured_time

    def get_status_revolve(self):
        event = ""
        for data in self._day_report['body_revolve']:
            if len(event) > 245:
                break
            if event != "":
                    event += " | "
            event += f"{datetime.datetime.fromtimestamp(data['time']).strftime('%-H:%M')} [{data['value']}]"

        if event == "":
            return "-"

        return event
        

    def get_status_body_move(self):
        event = ""
        for data in self._day_report['body_move']:
            if len(event) > 245:
                break

            if event != "":
                    event += " | "
            event += f"{datetime.datetime.fromtimestamp(data['time']).strftime('%-H:%M')} [{data['value']}]"

        if event == "":
            return "-"

        return event

    def get_status_vibrate_time(self):
        event = ""
        for data in self._day_report['snore']:
            if len(event) > 245:
                break

            if event != "":
                    event += " | "
            event += f"{datetime.datetime.fromtimestamp(data['time']).strftime('%-H:%M')} [{data['value']}]"

        if event == "":
            return "-"

        return event

    def get_status_snore_count_time(self):
        event = ""
        for data in self._day_report['snore_count']:
            if len(event) > 245:
                break

            if event != "":
                    event += " | "
            event += f"{datetime.datetime.fromtimestamp(data['time']).strftime('%-H:%M')} [{data['value']}]"

        if event == "":
            return "-"

        return event

        
    def get_status_vibrate_count(self):
        sum = 0
        for data in self._day_report['snore']:
            sum += data['value']

        return sum

    def get_status_snore_count(self):
        sum = 0
        for data in self._day_report['snore_count']:
            sum += data['value']

        return sum




    async def fetch_report_day(self, date: datetime):
        _LOGGER.debug("Fetch_report_day")

        # if (self._last_get_token is None or datetime.datetime.now() - self._last_get_token > datetime.timedelta(hours=2)):
        #     await self.refresh_token()

        url = "http://beacon5c.mirahome.net/beacon5/client/beacon/getday"
        target_day = date.strftime("%Y-%m-%d")
        # target_day = "2022-12-11"
        timestamp = self.timestamp()
        header = {"token": self._token}
        body = {"cname": self._cname, "tmsp": timestamp, "day": target_day, "did": self._did, "uid": self._uid, "timezone": 7}
        _LOGGER.debug(body)
        async with self._session.post(
            url, raise_for_status=True, headers=header, json=body
        ) as resp:
            resp_json = await resp.json()
            _LOGGER.debug(f"DATA From API {resp_json}")
            if int(resp_json["code"]) != 1000:
                _LOGGER.debug(f"Error - Resp code = {resp_json['code']}")
                raise web.HTTPUnauthorized(
                    reason=f"error code {resp_json['code']}"
                )
            data = resp_json["data"]
            
            self._day_report = data
            self._day_report["deep_sleep_time"] = self.get_status_sleep_time(STATE_DEEP_SLEEP)
            self._day_report["light_sleep_time"] = self.get_status_sleep_time(STATE_LIGHT_SLEEP)
            self._day_report["rem_time"] = self.get_status_sleep_time(STATE_REM_SLEEP)
            self._day_report["awake_time"] = self.get_status_sleep_time(STATE_AWAKE)
            self._day_report["revolve_time"] = self.get_status_revolve()
            self._day_report["move_time"] = self.get_status_body_move()
            self._day_report["vibrate_count"] = self.get_status_vibrate_count()
            self._day_report["vibrate_time"] = self.get_status_vibrate_time()
            self._day_report["snore_count_total"] = self.get_status_snore_count()
            self._day_report["snore_count_time"] = self.get_status_snore_count_time()
            return self._day_report

    async def fetch_last_night_report(self):
        yesterday_date = datetime.datetime.now() - datetime.timedelta(days=1)
        return await self.fetch_report_day(yesterday_date)

    @property
    def day_report(self):
        return self._day_report

    @property
    def did(self):
        return self._did
