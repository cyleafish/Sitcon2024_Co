import requests
import logging
import google.generativeai as genai
import os

def fetch_news_data(query, api_key):
    """
    Fetch news data from News API with a focus on Traditional Chinese (Taiwan) content.
    """
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}&language=zh&sortBy=publishedAt&country=tw"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch news data: {response.status_code}")
        return {"status": "error", "message": "無法獲取新聞數據"}

def generate_gmini_story(prompt, api_key, conversation_history=None):
    """
    Generate story using Google Gemini API.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    try:
        # 初始化消息历史
        messages = []
        
        # 如果存在对话历史，则将其添加到消息中
        if conversation_history:
            messages = conversation_history
        else:
            # 将初始的提示信息作为对话的一部分
            messages.append({'role': 'user', 'content': prompt})

        # 调用生成内容的方法
        response = model.generate_content(messages)
        
        # 提取生成的内容
        if response and response.generations:
            return response.generations[0].text
        else:
            logging.error("No generations found in response.")
            return "無法生成故事。"

    except Exception as e:
        logging.error(f"Failed to generate story: {e}")
        return "無法生成故事。"
