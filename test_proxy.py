from fp.fp import FreeProxy
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_proxy(proxy_url):
    try:
        session = requests.Session()
        session.proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Test the proxy
        response = session.get('https://api.ipify.org?format=json', timeout=10)
        response.raise_for_status()
        logger.info(f"Proxy working! IP: {response.json()['ip']}")
        return True
    except Exception as e:
        logger.error(f"Proxy failed: {str(e)}")
        return False

def main():
    logger.info("Finding working proxy...")
    
    for _ in range(5):  # Try 5 different proxies
        try:
            proxy = FreeProxy(
                rand=True,
                timeout=5,
                country_id=['US', 'CA', 'GB']  # Try to get proxies from these countries
            ).get()
            
            logger.info(f"Testing proxy: {proxy}")
            if test_proxy(proxy):
                print(f"\nWorking proxy found!\nProxy URL: {proxy}")
                break
        except Exception as e:
            logger.error(f"Error getting proxy: {str(e)}")
            continue

if __name__ == "__main__":
    main()

import unittest
from unittest.mock import patch, MagicMock
import requests
from config import Config
from main import get_scrapeops_url, make_request, get_truth_social_posts

class TestProxy(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.test_url = "https://truthsocial.com/api/v1/accounts/lookup"
        
    def test_scrapeops_url_generation(self):
        """Test ScrapeOps proxy URL generation"""
        proxy_url = get_scrapeops_url(self.test_url)
        self.assertTrue("proxy.scrapeops.io" in proxy_url)
        self.assertTrue("api_key=" in proxy_url)
        self.assertTrue("url=" in proxy_url)
        
    @patch('requests.get')
    def test_make_request_success(self, mock_get):
        """Test successful request with retry mechanism"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123"}
        mock_get.return_value = mock_response
        
        response = make_request(self.test_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": "123"})
        
    @patch('requests.get')
    def test_make_request_retry(self, mock_get):
        """Test request retry on failure"""
        mock_get.side_effect = [
            requests.exceptions.RequestException(),
            requests.exceptions.RequestException(),
            MagicMock(status_code=200)
        ]
        
        response = make_request(self.test_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_get.call_count, 3)
        
    @patch('main.make_request')
    def test_get_truth_social_posts(self, mock_make_request):
        """Test Truth Social posts retrieval"""
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {"id": "123"}
        
        mock_posts_response = MagicMock()
        mock_posts_response.json.return_value = [
            {
                "id": "1",
                "content": "Test post",
                "created_at": "2025-06-16T12:00:00Z"
            }
        ]
        
        mock_make_request.side_effect = [mock_user_response, mock_posts_response]
        
        posts = get_truth_social_posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["content"], "Test post")
        
if __name__ == '__main__':
    unittest.main()
