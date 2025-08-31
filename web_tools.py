import requests
from bs4 import BeautifulSoup

def simple_web_search(query):
    try:
        url = f"https://www.google.com/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        snippets = soup.find_all("span")
        result = " ".join([s.get_text() for s in snippets[:5]])
        return result
    except Exception as e:
        return f"Web search failed: {e}"
