from bs4 import BeautifulSoup
from pathlib import Path
import json
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def parse_eurlex_html(file_path: Path, regulation_name: str):
    logger.info(f"Parsing {file_path} for {regulation_name}...")
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    articles = []
    
    elements = soup.find_all(['p', 'div'])
    
    current_article = None
    
    for el in elements:
        text = el.get_text(strip=True)
        if not text:
            continue
            
        classes = el.get('class', [])
        
        # Heuristic for Article Start
        is_article_start = False
        if 'ti-art' in classes:
            is_article_start = True
        # Regex fallback for different HTML structures
        elif re.match(r"^Article\s+\d+$", text) and len(text) < 20: 
            is_article_start = True
            
        if is_article_start:
            if current_article:
                # Close previous
                current_article['full_text'] = "\n".join(current_article['text'])
                del current_article['text']
                articles.append(current_article)
            
            # Start new
            match = re.search(r"\d+", text)
            article_num = match.group(0) if match else "0"
            
            current_article = {
                "id": f"{regulation_name}_Article_{article_num}",
                "article_number": article_num,
                "title": "",
                "text": [],
                "regulation": regulation_name
            }
            continue
            
        if current_article:
            # Capture Content
            if 'sti-art' in classes:
                current_article['title'] = text
            elif 'oj-normal' in classes or 'normal' in classes:
                current_article['text'].append(text)
            elif el.name == 'p' and 'class' not in el.attrs:
                current_article['text'].append(text)
            elif el.name == 'li' or 'lij' in classes:
                current_article['text'].append(f"- {text}")

    # Append last
    if current_article:
        current_article['full_text'] = "\n".join(current_article['text'])
        del current_article['text']
        articles.append(current_article)
        
    logger.info(f"Found {len(articles)} articles in {regulation_name}")
    
    # Save
    output_file = PROCESSED_DIR / f"{regulation_name.lower()}_articles.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    
    return articles

if __name__ == "__main__":
    gdpr = parse_eurlex_html(RAW_DIR / "gdpr.html", "GDPR")
    ai_act = parse_eurlex_html(RAW_DIR / "ai_act.html", "EU_AI_Act")
    
    if gdpr:
        print(f"GDPR Articles: {len(gdpr)}")
    if ai_act:
        print(f"AI Act Articles: {len(ai_act)}")
