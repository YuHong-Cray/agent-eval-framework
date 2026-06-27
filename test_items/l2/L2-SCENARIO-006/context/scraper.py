"""Web scraper with caching ¡ª implement per requirements."""
import sys

def scrape(url: str) -> dict:
    # TODO: implement
    pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <url>")
        sys.exit(1)
    result = scrape(sys.argv[1])
    import json
    print(json.dumps(result, indent=2))
