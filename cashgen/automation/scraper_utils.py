# scraper_utils.py
import statistics
import sys, os, django, asyncio

sys.path.append("../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cashgen.settings")
django.setup()

from playwright.async_api import async_playwright

from pricing.models import MarketItem, CompetitorListing

IS_HEADLESS = False

SCRAPER_CONFIGS = {
    "CashConverters": {
        "base_url": "https://www.cashconverters.co.uk",
        "url": "https://www.cashconverters.co.uk/search-results?Sort=default&page=1"
               "&f%5Bcategory%5D%5B0%5D=all&f%5Blocations%5D%5B0%5D=all"
               "&query={model}%20{storage}",
        "price_class": ".product-item__price",
        "url_selector": ".product-item__title, .product-item__image a",
        "title_class": ".product-item__title__description",
        "shop_class": ".product-item__title__location",
        "detail_selectors": {
            "description_class": ".product-details__description",
        }
    },

    "CashGenerator": {
        "base_url": "https://cashgenerator.co.uk",  # <-- add this
        "url": "https://cashgenerator.co.uk/pages/search-results-page?q={model}%20{storage}",
        "url_selector": ".snize-view-link",
        "price_class": ".snize-price.money",
        "title_class": ".snize-title",
        "shop_class": ".snize-attribute",
        "detail_selectors": {
            "description_class": ".condition-box",
        }
    },

    "CEX": {
        "base_url": "https://uk.webuy.com",
        "url": "https://uk.webuy.com/search?stext={model}+{storage}",
        "price_class": ".product-main-price",
        "title_class": ".card-title",
        "url_selector": ".card-title a",
        "detail_selectors": {
            "description_class": ".item-description",
            "title_class": ".vendor-name"
        }
    },

    "eBay": {
        "base_url": "https://ebay.co.uk",
        "url": "https://www.ebay.co.uk/sch/i.html?_nkw={model}+{storage}&_sacat=0&_from=R40&_trksid=p4432023.m570.l1313",
        "price_class": ".s-card__price, .su-styled-text.primary.bold.large-1.s-card__price",
        "title_class": ".s-card__title",
        "url_selector": ".su-card-container__content > a",  # explicit first product link
    }
}


async def setup_page_optimization(page):
    """
    Optimize page loading by blocking unnecessary resources
    """
    # Block images, stylesheets, fonts, and other non-essential resources
    await page.route("**/*", lambda route: (
        route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"]
        else route.continue_()
    ))

    # Set a custom user agent to avoid bot detection
    await page.set_extra_http_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })


async def generic_scraper(
        url: str,
        competitor: str,
        model: str,
        storage: str,
        price_class: str,
        title_class: str,
        shop_class: str = None,
        exclude=None,
        filter_listings=None,
        summarise_prices=None,
        browser_context=None
):
    """
    Generic scraper for competitor websites.
    Returns (prices, titles, store_names, urls, summary).
    """
    page = await browser_context.new_page()

    await setup_page_optimization(page)

    try:
        await page.goto(url, wait_until='domcontentloaded')
        await page.wait_for_selector(price_class, timeout=15000)
    except Exception as e:
        print(f"Warning: prices not found for {competitor} within timeout: {e}")

    # --- MUCH FASTER: grab all texts in one call instead of per element ---
    titles = await page.eval_on_selector_all(
        title_class,
        "els => els.map(e => e.innerText.trim())"
    )

    prices_text = await page.eval_on_selector_all(
        price_class,
        "els => els.map(e => e.innerText.trim())"
    )
    prices = [parse_price(p) for p in prices_text if parse_price(p) is not None]

    # We still need element handles for URLs and store names
    title_elements = await page.query_selector_all(title_class)

    # --- Extract store names as before ---
    store_names = []
    if shop_class:
        try:
            await page.wait_for_selector(shop_class, timeout=2500)
        except:
            pass

        for t_elem in title_elements:
            try:
                shop_elem = await t_elem.query_selector(shop_class)
                if shop_elem:
                    store_text = (await shop_elem.inner_text()).strip() or None
                else:
                    store_text = await t_elem.evaluate("""
                        (el, sel) => {
                            let q = el.querySelector(sel);
                            if (q && q.innerText.trim()) return q.innerText.trim();
                            const containers = [
                                '.snize-overhidden', '.snize-view', '.product-item',
                                '.product-card', '.card', '.s-item__wrapper', '.su-card-container',
                                'article', '.product'
                            ];
                            for (const c of containers) {
                                const anc = el.closest(c);
                                if (anc) {
                                    q = anc.querySelector(sel);
                                    if (q && q.innerText.trim()) return q.innerText.trim();
                                }
                            }
                            let parent = el.parentElement;
                            while (parent) {
                                q = parent.querySelector(sel);
                                if (q && q.innerText.trim()) return q.innerText.trim();
                                parent = parent.parentElement;
                            }
                            return null;
                        }
                    """, shop_class)

                if store_text:
                    store_text = store_text.replace('\n', ' ').strip()
            except Exception:
                store_text = None

            store_names.append(store_text)

        while len(store_names) < len(titles):
            store_names.append(None)
    else:
        store_names = [None] * len(titles)

    if filter_listings:
        filtered_prices, filtered_titles, filtered_stores = [], [], []
        for price, title, store in zip(prices, titles, store_names):
            title_lower = title.lower()
            if model.lower() in title_lower and storage.lower() in title_lower:
                if not exclude or not any(term.lower() in title_lower for term in exclude):
                    filtered_prices.append(price)
                    filtered_titles.append(title)
                    filtered_stores.append(store)
        prices, titles, store_names = filtered_prices, filtered_titles, filtered_stores

    summary = summarise_prices(prices) if summarise_prices else {
        "Low": min(prices) if prices else None,
        "Mid": statistics.median(prices) if prices else None,
        "High": max(prices) if prices else None,
    }

    # --- Build URLs ---
    url_selector = SCRAPER_CONFIGS[competitor].get("url_selector")
    base_url = SCRAPER_CONFIGS[competitor].get("base_url", "")
    urls = []

    if url_selector:
        for t_elem in title_elements:
            href = await t_elem.get_attribute('href')
            if not href:
                a = await t_elem.query_selector('a')
                href = await a.get_attribute('href') if a else None
            if not href:
                try:
                    href = await t_elem.evaluate(
                        '(el, sel) => { const q = el.querySelector(sel); if (q) return q.getAttribute("href"); const c = el.closest(sel); return c ? c.getAttribute("href") : null }',
                        url_selector
                    )
                except Exception:
                    href = None

            if href and href.startswith("/") and base_url:
                href = base_url.rstrip('/') + href
            elif href and not href.startswith("http") and base_url:
                href = base_url.rstrip('/') + '/' + href
            urls.append(href)

        while len(urls) < len(titles):
            urls.append(None)
    else:
        urls = [None] * len(titles)

    try:
        await page.close()
    except Exception:
        pass

    return prices, titles, store_names, urls, summary

async def ebay_scraper(
        url: str,
        model: str,
        exclude=None,
        filter_listings=None,
        summarise_prices=None,
        browser_context=None
):
    """
    Specialized eBay scraper that matches prices to titles correctly (single loop per card).
    Now optimized with eval_on_selector_all to reduce async roundtrips.
    """
    page = await browser_context.new_page()

    # Apply optimizations
    await setup_page_optimization(page)

    try:
        await page.goto(url, wait_until='domcontentloaded')
        try:
            await page.wait_for_selector('.s-item__wrapper, .su-card-container, .s-item', timeout=10000)
        except:
            print("Warning: No eBay product wrapper found, proceeding anyway")
    except Exception as e:
        print(f"Warning: eBay content loading issue: {e}")

    print(url)

    # --- Grab card containers once ---
    card_containers = await page.query_selector_all('.s-item__wrapper, .su-card-container, .s-item')

    prices, titles, urls = [], [], []

    for card in card_containers:
        try:
            # --- Titles (faster eval inside card) ---
            title = await card.eval_on_selector(
                '.s-item__title, .s-card__title, .s-item__title-text',
                "el => el.innerText.trim()",
            )
            if not title or title.lower() in ['shop on ebay', '', 'new listing']:
                continue

            # --- Prices (grab all in one go) ---
            card_prices_text = await card.eval_on_selector_all(
                '.s-item__price, .s-card__price, .notranslate',
                "els => els.map(e => e.innerText.trim())",
            )
            card_prices = [parse_price(pt) for pt in card_prices_text if parse_price(pt) is not None]
            if not card_prices:
                continue

            main_price = card_prices[0]

            # --- URL (first link in card) ---
            href = await card.eval_on_selector("a", "el => el.getAttribute('href')") if await card.query_selector("a") else None

            prices.append(main_price)
            titles.append(title)
            urls.append(href)

        except Exception as e:
            print(f"Error processing eBay card: {e}")
            continue

    try:
        await page.close()
    except Exception:
        pass

    # Optional filtering
    if filter_listings:
        filtered_prices, filtered_titles, filtered_urls = [], [], []
        model_lower = model.lower()
        for price, title, u in zip(prices, titles, urls):
            title_lower = title.lower()
            if model_lower in title_lower:
                if not exclude or not any(term.lower() in title_lower for term in exclude):
                    filtered_prices.append(price)
                    filtered_titles.append(title)
                    filtered_urls.append(u)
        prices, titles, urls = filtered_prices, filtered_titles, filtered_urls

    summary = summarise_prices(prices) if summarise_prices else {
        "Low": min(prices) if prices else None,
        "Mid": statistics.median(prices) if prices else None,
        "High": max(prices) if prices else None,
    }

    return prices, titles, urls, summary


async def _scrape_competitor(browser_context, competitor, search_string, exclude, filter_listings, summarise_prices):
    config = SCRAPER_CONFIGS[competitor]

    # URL encoding for spaces
    query_str = search_string.replace(" ", "+" if competitor in ["CEX", "eBay"] else "%20")
    url = config["url"].format(model=query_str, storage="")  # storage ignored for now

    if competitor == "eBay":
        prices, titles, urls, summary = await ebay_scraper(
            url=url,
            model=search_string,
            exclude=exclude,
            filter_listings=filter_listings,
            summarise_prices=summarise_prices,
            browser_context=browser_context,   # <-- pass browser down
        )
        store_names = [None] * len(titles)
    else:
        prices, titles, store_names, urls, summary = await generic_scraper(
            url=url,
            competitor=competitor,
            model=search_string,
            storage="",
            price_class=config["price_class"],
            title_class=config["title_class"],
            shop_class=config.get("shop_class"),
            exclude=exclude,
            filter_listings=filter_listings,
            summarise_prices=summarise_prices,
            browser_context=browser_context,   # <-- pass browser down
        )

    return competitor, prices, titles, store_names, urls, summary


def save_prices(competitors, search_string, exclude=None, filter_listings=None, summarise_prices=None):
    """
    Run scraping for one or more competitors in parallel using a shared browser.
    competitors can be a string (single competitor) or list of competitor names.
    """
    if isinstance(competitors, str):
        competitors = [competitors]

    async def run_all():
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=IS_HEADLESS,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )

            # Create a browser context - this is what manages tabs
            browser_context = await browser.new_context()


            tasks = [
                _scrape_competitor(browser_context, comp, search_string, exclude, filter_listings, summarise_prices)
                for comp in competitors
            ]
            results = await asyncio.gather(*tasks)
            await browser.close()
            return results

    results = asyncio.run(run_all())

    # Save to DB
    item, _ = MarketItem.objects.get_or_create(title=search_string)

    summaries = {}
    for competitor, prices, titles, store_names, urls, summary in results:
        summaries[competitor] = summary
        for price, title, store, url_item in zip(prices, titles, store_names, urls):
            CompetitorListing.objects.update_or_create(
                market_item=item,
                competitor=competitor,
                title=title,
                defaults={
                    "price": price,
                    "store_name": store,
                    "url": url_item
                },
            )

    return summaries



def parse_price(text):
    """
    Parse price text to extract numeric value
    Handles various formats like '£188.95', '£188.95 to £219.95', etc.
    """
    try:
        # Handle price ranges by taking the first price
        if ' to ' in text:
            text = text.split(' to ')[0]

        # Remove currency symbols and clean up
        cleaned = text.replace("£", "").replace(",", "").replace("(", "").replace(")", "").strip()

        # Extract just the numeric part (handles cases like "£188.95/Unit")
        import re
        match = re.search(r'\d+\.?\d*', cleaned)
        if match:
            return float(match.group())

        return None
    except:
        return None


def filter_listings(prices, titles, search_string="", exclude=None):
    if exclude is None:
        exclude = []
    if isinstance(exclude, str):
        exclude = [exclude]
    filtered_prices = []
    filtered_titles = []
    for price, title in zip(prices, titles):
        title_lower = title.lower()
        if search_string.lower() in title_lower:
            if not any(term.lower() in title_lower for term in exclude):
                filtered_prices.append(price)
                filtered_titles.append(title)
    return filtered_prices


def summarise_prices(prices):
    if not prices:
        return {"Low": None, "Mid": None, "High": None}
    low = min(prices)
    mid = statistics.median(prices)
    high = max(prices)
    return {"Low": low, "Mid": mid, "High": high}


async def extract_prices_and_titles(page, price_class=".product-item__price",
                                    title_class=".product-item__title__description"):
    price_elements = await page.query_selector_all(price_class)
    prices_text = [await e.inner_text() for e in price_elements]
    prices = [parse_price(p) for p in prices_text if parse_price(p) is not None]

    title_elements = await page.query_selector_all(title_class)
    titles = [await e.inner_text() for e in title_elements]

    return prices, titles