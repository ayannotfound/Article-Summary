import requests
from bs4 import BeautifulSoup
import nltk
from newspaper import Article
import argparse
import sys
import os

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


def extract_article(url):
    """Extract article content using newspaper3k."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()
        base_summary = article.summary
        if article.text:
            sentences = nltk.sent_tokenize(article.text)
            summary_sentences = nltk.sent_tokenize(base_summary)
            summary_sentence_set = set(summary_sentences)
            extended_summary = summary_sentences.copy()
            for sentence in sentences:
                if sentence not in summary_sentence_set and len(extended_summary) < 10:
                    extended_summary.append(sentence)
                    summary_sentence_set.add(sentence)
            extended_summary_text = ' '.join(extended_summary)
        else:
            extended_summary_text = base_summary
        return {
            'title': article.title,
            'text': article.text,
            'summary': extended_summary_text,
            'keywords': article.keywords
        }
    except Exception as e:
        print(f"Error extracting article: {e}")
        return None

def fallback_scrape(url):
    """Fallback method to scrape article content if newspaper3k fails."""
    try:
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
        sentences = nltk.sent_tokenize(content)
        summary = ' '.join(sentences[:min(7, len(sentences))])
        return {
            'title': title,
            'text': content,
            'summary': summary,
            'keywords': []
        }
    except Exception as e:
        print(f"Error with fallback scrape: {e}")
        return None

def process_article(url):
    """Process an article URL - extract content and summary."""
    article_data = extract_article(url)
    if not article_data:
        print("Primary extraction failed, trying fallback method...")
        article_data = fallback_scrape(url)
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
    parser = argparse.ArgumentParser(description='Scrape and summarize a news article.')
    parser.add_argument('url', help='URL of the news article to scrape and summarize')
    parser.add_argument('--full', action='store_true', help='Display the full article text')
    args = parser.parse_args()
    article_data = process_article(args.url)
    if article_data:
        display_article(article_data)
        if args.full:
            print(f"\nFULL ARTICLE TEXT:\n{'-'*80}\n{article_data['text']}")

if __name__ == "__main__":
    main()
