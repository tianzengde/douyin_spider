from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from pydantic import BaseModel
from typing import List
import json
import time
import datetime


class SpiderDY(object):

    def __init__(self) -> None:
        caps = DesiredCapabilities.CHROME
        caps["goog:loggingPrefs"] = {"performance": "ALL"}
        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Chrome(options=options)
        self.driver = webdriver.Chrome(desired_capabilities=caps)

    def search_user(self, account) -> str:
        url = f"https://www.douyin.com/search/{account}"
        self.driver.get(url)
        user_btn_xp = '//*[@id="dark"]/div[2]/div/div[1]/div[1]/div[2]/span[3]'
        user_btn = self.driver.find_element(By.XPATH, user_btn_xp)
        user_btn.click()
        time.sleep(3)
        user_div_xp = '//*[@id="dark"]/div[2]/div/div[2]/div[3]/ul/li[1]/div/a'
        user_div = self.driver.find_element(By.XPATH, user_div_xp)
        href = user_div.get_attribute("href")
        return href

    def process_browser_log_entry(self, entry):
        response = json.loads(entry["message"])["message"]
        return response

    def network_respanse(self, requestId):
        result = self.driver.execute_cdp_cmd(
            'Network.getResponseBody', {'requestId': requestId})
        body_str = result.get("body")
        respanse = json.loads(body_str)
        return respanse

    def user_info(self, url: str, **kwargs) -> dict:
        self.driver.get(url=url)
        browser_log = self.driver.get_log("performance")
        events = [self.process_browser_log_entry(
            entry) for entry in browser_log]
        events = [event for event in events if event.get(
            "method") in ["Network.responseReceived"]]
        requestId = ""
        for e in events:
            if "aweme/v1/web/user/profile/other/" in e.get("params").get("response").get("url"):
                requestId = e["params"]["requestId"]
        resp_result = self.driver.execute_cdp_cmd(
            'Network.getResponseBody', {'requestId': requestId})
        body_str = resp_result.get("body")
        resp_result = json.loads(body_str)
        nickname = resp_result.get("user").get("nickname")
        if kwargs.get("download", False):
            with open(f"userInfo/{nickname}.json", "w", encoding="utf8") as f:
                f.write(body_str)
        return resp_result

    def scrolled_bottom(self):
        last_height = self.driver.execute_script(
            "return document.body.scrollHeight")
        while True:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight*0.90);")

            time.sleep(1)

            new_height = self.driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def videos_info(self, url: str, **kwargs) -> list:
        self.driver.get(url=url)
        time.sleep(1)
        self.scrolled_bottom()
        browser_log = self.driver.get_log("performance")
        events = [self.process_browser_log_entry(
            entry) for entry in browser_log]
        events = [event for event in events if event.get(
            "method") in ["Network.responseReceived"]]
        requestIds = []
        for e in events:
            if "aweme/v1/web/aweme/post/" in e.get("params").get("response").get("url"):
                requestIds.append(e["params"]["requestId"])
        videos_resp = []
        for r in requestIds:
            videos_resp = videos_resp + \
                (self.network_respanse(r)).get("aweme_list")

        if kwargs.get("download", False):
            with open(f"video.json", "w", encoding="utf8") as f:
                f.write(json.dumps(videos_resp))
        return videos_resp

    def close(self):
        self.driver.close()


class VideoPydtc(BaseModel):
    aweme_id: str | int
    video_id: str | int
    author_user_id: str | int
    create_time: datetime.datetime
    desc: str
    preview_title: str
    share_url: str
    statistics: dict
    download_addr: list
    origin_cover: list | None
    spider_time: datetime.datetime


class UserPydtc(BaseModel):
    uid: str | int
    unique_id: str | int
    nickname: str
    signature: str
    user_age: str | int
    sec_uid: str
    ip_location: str
    follower_count: str | int
    following_count: str | int
    total_favorited: str | int
    share_url: str
    share_qrcode_url: list
    avatar: dict


def video_filtering(videos: list) -> List[VideoPydtc]:
    filted_videos = []
    for v in videos:
        info = {
            "aweme_id": v.get("aweme_id"),
            "video_id": v.get("aweme_id"),
            "author_user_id": v.get("author_user_id"),
            "create_time": datetime.datetime.fromtimestamp(v.get("create_time")) + datetime.timedelta(hours=8),
            "desc": v.get("desc"),
            "preview_title": v.get("preview_title"),
            "share_url": v.get("share_url"),
            "statistics": v.get("statistics"),
            "download_addr": v.get("video").get("download_addr").get("url_list"),
            "origin_cover": v.get("video").get("origin_cover").get("url_list"),
            "spider_time": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        }
        video_dtc = VideoPydtc(**info)
        filted_videos.append(video_dtc)
    return filted_videos


def user_filtering(user_info: dict) -> UserPydtc:
    fields = UserPydtc.__fields__.keys()
    user_info = user_info.get("user")
    info = {k: user_info.get(k, None) for k in fields}
    share = user_info.get("share_info")
    info["share_url"] = share.get("share_url")
    info["share_qrcode_url"] = share.get("share_qrcode_url").get("url_list")
    avatar = {
        "avatar_168x168": user_info.get("avatar_168x168").get("url_list")[0],
        "avatar_300x300": user_info.get("avatar_300x300").get("url_list")[0],
        "avatar_1080x1080": user_info.get("avatar_larger").get("url_list")[0],
        "avatar_720x720": user_info.get("avatar_medium").get("url_list")[0],
        "avatar_100x100": user_info.get("avatar_thumb").get("url_list")[0],
    }
    info["avatar"] = avatar
    return UserPydtc(**info)


if __name__ == "__main__":

    url = "https://www.douyin.com/user/MS4wLjABAAAAB8Wx_ofNp4FZgxp6hb5IRLDu4t8mfT9eBlZShcMt1MoAY1w7IoZctmFeYgxf7I9C?vid=7096823142139677966"
    # "https://www.douyin.com/aweme/v1/web/comment/list/" # 评论

    dy = SpiderDY()

    # user_url = dy.search_user("24481641751")

    user_info = dy.user_info(url=url)
    user_pydtc = user_filtering(user_info)

    # videos_info = dy.videos_info(url=url)
    # videos_pydtc = video_filtering(videos_info)

    dy.close()
