import requests
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

URLS = {
    "gdpr.html": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679",
    "ai_act.html": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689"
}

def download_file(filename: str, url: str):
    logger.info(f"Downloading {filename} from {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        file_path = DATA_DIR / filename
        file_path.write_text(response.text, encoding="utf-8")
        logger.info(f"Successfully saved {filename} ({len(response.text)} characters)")
        
    except Exception as e:
        logger.error(f"Failed to download {filename}: {e}")

if __name__ == "__main__":
    for name, url in URLS.items():
        download_file(name, url)
