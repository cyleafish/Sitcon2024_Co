import requests

def fetch_news_data(query, api_key):
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    return response.json()

def generate_gmini_story(prompt, user_id, api_key):
    url = "https://api.gmini.ai/generate"
    payload = {"prompt": prompt, "user_id": user_id, "api_key": api_key}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # 如果響應狀態碼不是 200，則引發 HTTPError
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to generate story: {e}")
        return {"error": "無法生成故事。"}
