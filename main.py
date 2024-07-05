import os
import sys
import logging
import requests
from fastapi import FastAPI, HTTPException, Request
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
from utils import fetch_news_data, generate_gmini_story

if os.getenv('API_ENV') != 'production':
    from dotenv import load_dotenv
    load_dotenv()

logging.basicConfig(level=os.getenv('LOG', 'WARNING'))
logger = logging.getLogger(__file__)

app = FastAPI()

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None or channel_access_token is None:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    sys.exit(1)

configuration = Configuration(access_token=channel_access_token)
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)

news_api_key = os.getenv('NEWS_API_KEY')
gmini_api_key = os.getenv('GMINI_API_KEY')

# Initialize the Gemini Pro API
#gmini.configure(api_key=GEMINI_API_KEY)

@app.get("/health")
async def health():
    return 'ok'

import random

async def process_user_message(message, user_id):
    """
    處理用戶發送的消息並返回相應的回應。
    """
    if "新聞" in message:
        # 呼叫 fetch_news_data 函數來獲取新聞
        news_response = fetch_news_data("gender equality OR emotional education", news_api_key)
        if news_response and news_response.get("status") == "ok":
            articles = news_response.get("articles", [])
            if articles:
                random_article = random.choice(articles)
                return f"最新新聞：\n\n標題: {top_article['title']}\n\n描述: {top_article['description']}\n\n更多詳情: {top_article['url']}"
        return "目前沒有相關新聞。"
    elif "故事" in message:
        # 呼叫 generate_gmini_story 函數來生成故事
        story_response = generate_gmini_story("開始你的故事...", user_id, gmini_api_key)
        if story_response:
            return story_response.get("story", "無法生成故事。")
        return "生成故事時出現錯誤。"
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
    import uvicorn
    port = int(os.environ.get('PORT', default=8080))
    debug = os.environ.get('API_ENV', default='develop') == 'develop'
    logging.info('Application will start...')
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug)
