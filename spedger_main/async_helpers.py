import httpx, asyncio
from .slip_helpers import validate_url, PREVIEW_HEADERS, get_url


sem = asyncio.Semaphore(20)

async def scrape_site(url, platform, client):
    headers = PREVIEW_HEADERS.get(platform)

    if not headers:
        return (False, f"Unknown platform '{platform}'")
    
    error_txt = validate_url(url, platform)
    if error_txt != '':
        return (False, error_txt)
    
    try:
        async with sem:
            response = await client.get(url, headers = headers)
        response.raise_for_status()
        data = response.json()
        scrape_msg = data.get('message')

        if scrape_msg != 'Success':
            return (False, scrape_msg)
        return (True, data)

    except httpx.RequestError as e:
        return (False, f'Request failed: {e}')
    except Exception as e:
        return (False, f'Unexpected Error: {str(e)}')
    

async def scrape_slips_info(codes_tuple):
    urls = [get_url(code[0], 'sportybet') for code in codes_tuple]

    async with httpx.AsyncClient() as client:
        scraping_tasks = [scrape_site(url, 'sportybet', client) for url in urls ]
        scraping_results = await asyncio.gather(*scraping_tasks)

    return scraping_results   # no need to await the results again as results have already been gotten by the await asyncio.gather