import requests

def fetch_news_data(query, api_key):
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    return response.json()

def generate_gmini_story(prompt, user_id, api_key):
    url = f"https://api.gmini.ai/generate"
    payload = {"prompt": prompt, "user_id": user_id, "api_key": api_key}
    response = requests.post(url, json=payload)
    return response.json()
