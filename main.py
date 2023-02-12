from fastapi import FastAPI
from dy_spider import SpiderDY, user_filtering, video_filtering


app = FastAPI()


@app.get("/")
async def hello():
    return {"msg": "hello word"}


@app.get("/douyin/user/")
async def feach_user(url: str):
    dy = SpiderDY()
    user_info = dy.user_info(url=url)
    user_pydtc = user_filtering(user_info)
    dy.close()
    return user_pydtc.dict()


@app.get("/douyin/user/search/{user_id}")
async def feach_user(user_id: int | str):
    dy = SpiderDY()
    url = dy.search_user(account=user_id)
    dy.close()
    return {"msg": "ok", "url": url, "code":200}


@app.get("/douyin/user/video/")
async def feach_user(url: str):
    dy = SpiderDY()
    videos_info = dy.videos_info(url=url)
    videos = video_filtering(videos_info)
    dy.close()
    return videos
