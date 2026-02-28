import aiohttp
from bs4 import BeautifulSoup
import re

async def scrape_url(url: str) -> str:
    """Scrapes a URL and returns the visible text."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return f"Error: HTTP {response.status}"
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(separator=' ')
                # condense whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                # Return first 5000 characters to prevent huge context
                return text[:5000]
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
