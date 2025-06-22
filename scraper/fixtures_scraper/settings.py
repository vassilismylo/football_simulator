# Scrapy settings for fixtures_scraper project

BOT_NAME = 'fixtures_scraper'

SPIDER_MODULES = ['fixtures_scraper.spiders']
NEWSPIDER_MODULE = 'fixtures_scraper.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure delays for requests
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# Configure user agent
USER_AGENT = 'fixtures_scraper (+http://www.yourdomain.com)'

# Configure pipelines
ITEM_PIPELINES = {
    'fixtures_scraper.pipelines.FixturesPipeline': 300,
}

# Configure logging
LOG_LEVEL = 'INFO'

# Configure caching (helpful for development)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour

# Configure AutoThrottle for respectful scraping
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Disable cookies and telnet console
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False