"""Reviewed, unauthenticated public RSS endpoints; never caller-supplied URLs.

Official publisher listings and live HTTP 200 checks verified on 2026-10-27.
Feed access is not permission to redistribute full articles or use every feed
commercially. This collector retains publisher-supplied titles and summaries.
"""

CATALOG = {
    "nvidia-news": {
        "key": "nvidia-news", "name": "NVIDIA newsroom", "publisher": "NVIDIA",
        "url": "https://nvidianews.nvidia.com/releases.xml",
        "description": "Company-authored NVIDIA announcements. The publisher limits its RSS service to individual, non-commercial information use.",
        "reference_url": "https://www.nvidia.com/en-us/about-nvidia/rss/",
    },
    "aws-news": {
        "key": "aws-news", "name": "AWS news blog", "publisher": "Amazon Web Services",
        "url": "https://aws.amazon.com/blogs/aws/feed/",
        "description": "Company-authored cloud and product announcements from Amazon Web Services; not comprehensive Amazon company or earnings coverage.",
        "reference_url": "https://aws.amazon.com/blogs/aws/heads-up-aws-news-blog-rss-feed-change/",
    },
    "fed-monetary": {
        "key": "fed-monetary", "name": "Federal Reserve monetary policy", "publisher": "Federal Reserve Board",
        "url": "https://www.federalreserve.gov/feeds/press_monetary.xml",
        "description": "US monetary policy press releases and meeting-related announcements from the Federal Reserve Board.",
        "reference_url": "https://www.federalreserve.gov/feeds/feeds.htm",
    },
    "ecb-press": {
        "key": "ecb-press", "name": "European Central Bank press", "publisher": "European Central Bank",
        "url": "https://www.ecb.europa.eu/rss/press.html",
        "description": "ECB press releases, speeches, interviews and press conference transcripts for euro-area economic context.",
        "reference_url": "https://www.ecb.europa.eu/home/html/rss.en.html",
    },
    "eu-council": {
        "key": "eu-council", "name": "Council of the EU press", "publisher": "Council of the European Union",
        "url": "https://www.consilium.europa.eu/en/rss/pressreleases.ashx",
        "description": "Official EU Council decisions and statements, including international relations, sanctions and economic policy; not complete global news coverage.",
        "reference_url": "https://www.consilium.europa.eu/en/about-site/rss/",
    },
    "eia-energy": {
        "key": "eia-energy", "name": "EIA Today in Energy", "publisher": "US Energy Information Administration",
        "url": "https://www.eia.gov/rss/todayinenergy.xml",
        "description": "Energy facts, issues and trends published by the US Energy Information Administration.",
        "reference_url": "https://www.eia.gov/tools/rssfeeds/",
    },
}
