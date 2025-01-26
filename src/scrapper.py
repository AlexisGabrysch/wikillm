import requests
from bs4 import BeautifulSoup
from database import populate_chromadb

def scrape_wikipedia_fr(keyword):
    url = f"https://fr.wikipedia.org/wiki/{keyword.replace(' ', '_')}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", {"class": "mw-parser-output"})
        if content:
            paragraph = content.find("p")
            return paragraph.get_text(strip=True) if paragraph else None
    return None

if __name__ == "__main__":
    keywords = ["Seconde Guerre mondiale", "Révolution française"]
    scraped_data = {k: scrape_wikipedia_fr(k) for k in keywords}
    populate_chromadb(scraped_data)
