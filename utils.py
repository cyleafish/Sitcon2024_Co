import requests
import logging
import google.generativeai as genai
import os

def fetch_news_data(query, api_key):
    """
    Fetch news data from News API with a focus on Traditional Chinese (Taiwan) content.
    """
    # 指定语言为繁体中文（zh），国家为台湾（tw）
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch news data: {response.status_code}")
        return {"status": "error", "message": "無法獲取新聞數據"}

def generate_gmini_story(prompt, api_key):
    """
    Generate story using Google Gemini API.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    try:
       
        response = model.generate_content(prompt)
        # 提取生成的内容
        if response and response.text:
            return response.text
        else:
            logging.error("No generations found in response.")
            return "無法生成故事。"

    except Exception as e:
        logging.error(f"Failed to generate story: {e}")
        return "無法生成故事。"
