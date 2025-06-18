import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://playwright.dev")
        print(await page.title())
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())