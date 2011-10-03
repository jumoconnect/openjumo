from crawler import WebCrawler
from miner.web.etl import html_to_story

class SocialMediaCrawler(WebCrawler):
    
    def fetch_url(self, url):
        data = super(SocialMediaCrawler, self).fetch_url(url) if url else ''
        if data:
            data = html_to_story(data)
        
        return data