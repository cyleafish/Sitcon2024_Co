import os
import re
import sys
import requests
import logging
from fastapi import FastAPI, HTTPException, Request
from datetime import datetime
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import google.generativeai as genai
from firebase import firebase
from utils import check_location_in_message, get_current_weather, get_weather_data, simplify_data

# 如果不是在生產環境中，則載入 .env 文件中的環境變量
if os.getenv('API_ENV') != 'production':
    from dotenv import load_dotenv
    load_dotenv()

# 配置日誌記錄
logging.basicConfig(level=os.getenv('LOG', 'WARNING'))
logger = logging.getLogger(__file__)

app = FastAPI()

# 獲取 LINE Bot 所需的配置
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

configuration = Configuration(access_token=channel_access_token)
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)

# 配置 Gemini AI 和 Firebase
firebase_url = os.getenv('FIREBASE_URL')
gemini_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=gemini_key)

# 獲取 News API Key
news_api_key = os.getenv('NEWS_API_KEY')

@app.get("/health")
async def health():
    return 'ok'

def fetch_news(query="gender equality OR emotional education"):
    """
    使用 News API 獲取與性別平等和情感教育相關的最新新聞。
    """
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={news_api_key}"
    response = requests.get(url)
    news_data = response.json()

    if news_data.get("status") == "ok" and news_data.get("articles"):
        articles = news_data["articles"]
        # 選擇第一篇文章來展示
        top_article = articles[0]
        title = top_article["title"]
        description = top_article["description"]
        article_url = top_article["url"]

        return f"最新新聞：\n\n標題: {title}\n描述: {description}\n\n更多詳情: {article_url}"
    else:
        return "目前沒有相關新聞。"

async def generate_story(user_id):
    """
    根據用戶 ID 使用 Gemini AI 生成互動故事。
    """
    fdb = firebase.FirebaseApplication(firebase_url, None)
    user_chat_path = f'state/{user_id}'
    chat_state = fdb.get(user_chat_path, None)

    # 根據用戶之前的對話狀態生成故事情節
    if chat_state is None:
        story_intro = "歡迎！我們將開始一個關於性別平等和情感教育的故事。你願意加入嗎？"
        fdb.put_async(user_chat_path, None, {'stage': 'intro'})
    else:
        # 基於聊天狀態進行故事生成
        story_intro = "這裡可以根據之前的對話生成故事的下一步..."

    return story_intro

async def process_user_message(message, user_id):
    """
    處理用戶發送的消息並返回相應的回應。
    """
    # 檢查用戶是否詢問新聞或故事
    if "新聞" in message:
        # 呼叫 fetch_news 函數來獲取新聞
        news_response = fetch_news()
        return news_response
    elif "故事" in message:
        # 呼叫 generate_story 函數來生成故事
        return await generate_story(user_id)
    else:
        return "請問你想了解什麼？可以說「新聞」或「故事」。"

@app.post("/webhooks/line")
async def handle_callback(request: Request):
    """
    處理來自 LINE Bot 的 Webhook 回調請求。
    """
    signature = request.headers['X-Line-Signature']
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        logging.info(event)
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue
        
        text = event.message.text
        user_id = event.source.user_id

        reply_message = await process_user_message(text, user_id)
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_message)]
            )
        )

    return 'OK'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', default=8080))
    debug = True if os.environ.get('API_ENV', default='develop') == 'develop' else False
    logging.info('Application will start...')
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug)
