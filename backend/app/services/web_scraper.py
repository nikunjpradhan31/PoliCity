import aiohttp
from bs4 import BeautifulSoup
from tenacity import retry, wait_exponential, stop_after_attempt
import logging

logger = logging.getLogger(__name__)

class WebScraper:
    @staticmethod
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    async def fetch_html(url: str, user_agent: str = "Mozilla/5.0") -> str:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": user_agent}
            async with session.get(url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                return await response.text()

    @staticmethod
    async def get_text_from_url(url: str) -> str:
        try:
            html = await WebScraper.fetch_html(url)
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text(separator=" ", strip=True)
            return text
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return ""

    @staticmethod
    async def google_search_urls(query: str, num_results: int = 3) -> list:
        # Placeholder for actual Google Search API or scraping
        # We simulate finding URLs for a query
        return [f"https://example.com/search?q={query.replace(' ', '+')}"]
