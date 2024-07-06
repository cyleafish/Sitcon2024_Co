import os
import sys
import logging
import random
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

# 配置 API Key
news_api_key = os.getenv('NEWS_API_KEY')
gmini_api_key = os.getenv('GEMINI_API_KEY')

@app.get("/health")
async def health():
    return 'ok'

async def process_user_message(message, user_id):
    """
    處理用戶發送的消息並返回相應的回應。
    """
    try:
        if "新聞" in message:
            # 呼叫 fetch_news_data 函數來獲取新聞
            news_response = fetch_news_data("性別歧視", news_api_key)
            if news_response and news_response.get("status") == "ok":
                articles = news_response.get("articles", [])
                if articles:
                    top_article = articles[0]
                    return f"最新新聞：\n\n標題: {top_article['title']}\n描述: {top_article['description']}\n\n更多詳情: {top_article['url']}"
                    
        elif "更多" in message:
            news_response = fetch_news_data("性別", news_api_key)
            if news_response and news_response.get("status") == "ok":
                newsNo = random.randint(1, 50)
                articles = news_response.get("articles", [newsNo])
                if articles:
                    top_article = articles[newsNo]
                    return f"最新新聞：\n\n標題: {top_article['title']}\n描述: {top_article['description']}\n\n更多詳情: {top_article['url']}"
        
            return "目前沒有相關新聞。"

        elif "故事" in message:
            # 生成基於新聞的故事
            response = await generate_story_based_on_news(news_api_key, gmini_api_key)
            return response if response else "生成故事時出現錯誤。"
        
        else:
            # 生成基於用戶輸入的通用回應
            response = generate_gmini_story(prompt=message, api_key=gmini_api_key)
            return response if response else "無法生成回應。"

    except Exception as e:
        logging.error(f"Error processing user message: {e}")
        return "處理您的請求時出現錯誤。"

async def generate_story_based_on_news(news_api_key, gmini_api_key):
    """
    基於隨機選擇的新聞生成故事。
    """
    try:
        news_response = fetch_news_data("性別平等", news_api_key)
        if news_response and news_response.get("status") == "ok":
            articles = news_response.get("articles", [])
            if articles:
                random_article = articles[random.randrange(len(articles))]
                news_title = random_article.get("title")
                news_description = random_article.get("description")
                news_url = random_article.get("url")

                # 生成故事
                prompt = f"你是一位性別平等和情感教育老師，你要教導國小生性別平等和情感教育，根據新聞「{news_title}」描述: {news_description} \n生成一個互動故事給學生，在故事中要有選項給學生做選擇"
               
                story_response = generate_gmini_story(prompt, gmini_api_key)
                
                if story_response:
                    story_text = story_response
                    response = f"新聞：\n\n標題: {news_title}\n\n描述: {news_description}\n\n故事：\n{story_text}\n\n更多詳情: {news_url}"
                    return response
        return None

    except Exception as e:
        logging.error(f"Error generating story: {e}")
        return None

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
