import requests
import argparse
import sys
import os
from dotenv import load_dotenv
load_dotenv()

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

def summarize_text(text, api_key, max_chars=2000):
    safe_text = text[:max_chars]
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": safe_text,
        "parameters": {
            "min_length": 120,  
            "max_length": 300   
        }
    }
    response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and 'summary_text' in result[0]:
            return result[0]['summary_text']
        elif isinstance(result, dict) and 'error' in result:
            print(f"Hugging Face API error: {result['error']}")
            return None
    else:
        print(f"Failed to summarize: {response.status_code} {response.text}")
        return None

def extract_article_text(url):
    """Extract article content using requests and BeautifulSoup."""
    try:
        from bs4 import BeautifulSoup
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1')
        title = title.text.strip() if title else "No title found"
        content = None
        for selector in [
            'article', '.article-content', '.article-body', '.story-body',
            '.content', '.story', '.post-content', '[itemprop="articleBody"]']:
            content_element = soup.select_one(selector)
            if content_element:
                for script in content_element.find_all(['script', 'style']):
                    script.decompose()
                content = content_element.get_text(separator='\n').strip()
                break
        if not content:
            paragraphs = soup.find_all('p')
            content = '\n'.join([p.get_text().strip() for p in paragraphs])
        return {
            'title': title,
            'text': content
        }
    except Exception as e:
        print(f"Error extracting article: {e}")
        return None

def process_article(url, api_key=None):
    """Process an article URL - extract content and summarize using Hugging Face API."""
    if api_key is None:
        api_key = os.getenv('HUGGINGFACE_API_KEY')
    if not api_key:
        print("HUGGINGFACE_API_KEY environment variable not set.")
        return None
    article_data = extract_article_text(url)
    if not article_data:
        return None
    summary = summarize_text(article_data['text'], api_key)
    if not summary:
        print("Summarization failed.")
        return None
    article_data['summary'] = summary
    article_data['keywords'] = []
    return article_data

def display_article(article_data):
    """Display the article data in a formatted way."""
    if not article_data:
        print("Could not extract article data.")
        return
    print(f"\n{'='*80}\nTITLE: {article_data['title']}\n{'='*80}")
    print(f"\nSUMMARY:\n{'-'*80}\n{article_data['summary']}")
    if article_data['keywords']:
        print(f"\nKEYWORDS:\n{', '.join(article_data['keywords'])}")
    print(f"\n{'='*80}")

def main():
    parser = argparse.ArgumentParser(description='Scrape and summarize a news article using Hugging Face API.')
    parser.add_argument('url', help='URL of the news article to scrape and summarize')
    parser.add_argument('--full', action='store_true', help='Display the full article text')
    args = parser.parse_args()
    load_dotenv()
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    if not api_key:
        print("HUGGINGFACE_API_KEY environment variable not set.")
        sys.exit(1)
    article_data = process_article(args.url, api_key)
    if article_data:
        display_article(article_data)
        if args.full:
            print(f"\nFULL ARTICLE TEXT:\n{'-'*80}\n{article_data['text']}")

if __name__ == "__main__":
    main()
