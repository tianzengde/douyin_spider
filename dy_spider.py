from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
import json
import time


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


    def search_user(self, account) -> str :
        url = f"https://www.douyin.com/search/{account}"
        self.driver.get(url)
        user_btn_xp = '//*[@id="dark"]/div[2]/div/div[1]/div[1]/div[2]/span[3]'
        user_btn = self.driver.find_element(By.XPATH,user_btn_xp)
        user_btn.click()
        time.sleep(3)
        user_div_xp = '//*[@id="dark"]/div[2]/div/div[2]/div[3]/ul/li[1]/div/a'
        user_div = self.driver.find_element(By.XPATH,user_div_xp)
        href = user_div.get_attribute("href")
        return href


    def process_browser_log_entry(self, entry):
        response = json.loads(entry["message"])["message"]
        return response


    def user_info(self, url: str, **kwargs) -> dict:
        self.driver.get(url=url)
        browser_log = self.driver.get_log("performance") 
        events = [self.process_browser_log_entry(entry) for entry in browser_log]
        events = [event for event in events if event.get("method") in ["Network.responseReceived"]]
        requestId = ""
        for e in events:
            if "aweme/v1/web/user/profile/other/" in  e.get("params").get("response").get("url"):
                requestId = e["params"]["requestId"]
        resp_result = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': requestId})
        body_str = resp_result.get("body")
        resp_result = json.loads(body_str)
        nickname = resp_result.get("user").get("nickname")
        if kwargs.get("download", False):
            with open(f"userInfo/{nickname}.json","w",encoding="utf8") as f:
                f.write(body_str)
        return resp_result
    

    def close(self):
        self.driver.close()


url = "https://www.douyin.com/user/MS4wLjABAAAAB8Wx_ofNp4FZgxp6hb5IRLDu4t8mfT9eBlZShcMt1MoAY1w7IoZctmFeYgxf7I9C?vid=7096823142139677966"

dy = SpiderDY()
user_url = dy.search_user("24481641751")
user_info = dy.user_info(url=user_url,download=True)
dy.close()