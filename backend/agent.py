import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

# Gemini fallback ke liye
from browser_use import Agent, Browser, BrowserConfig

from langchain_google_genai import ChatGoogleGenerativeAI

CONTACT_PATHS = [
    '/contact', '/contact-us', '/contact_us', '/contactus',
    '/get-in-touch', '/reach-us', '/reach-out', '/connect',
    '/about/contact', '/about-us/contact', '/say-hello',
    '/talk-to-us', '/write-to-us', '/enquiry', '/inquiry'
]

NAME_SELECTORS = [
    'input[name*="name" i]:not([name*="last" i]):not([name*="user" i])',
    'input[id*="your-name" i]', 'input[placeholder*="your name" i]',
    'input[id*="fullname" i]', 'input[id*="full_name" i]',
    'input[placeholder*="full name" i]', 'input[id*="fname" i]',
    'input[name="name"]', 'input[id="name"]',
]

EMAIL_SELECTORS = [
    'input[type="email"]', 'input[name*="email" i]',
    'input[id*="email" i]', 'input[placeholder*="email" i]',
]

PHONE_SELECTORS = [
    'input[type="tel"]', 'input[name*="phone" i]',
    'input[name*="mobile" i]', 'input[id*="phone" i]',
    'input[placeholder*="phone" i]', 'input[placeholder*="mobile" i]',
    'input[name*="tel" i]',
]

MESSAGE_SELECTORS = [
    'textarea[name*="message" i]', 'textarea[id*="message" i]',
    'textarea[placeholder*="message" i]', 'textarea[name*="comment" i]',
    'textarea[name*="query" i]', 'textarea[name*="description" i]',
    'textarea', 
]

SUBMIT_SELECTORS = [
    'input[type="submit"]', 'button[type="submit"]',
    'button:has-text("Send")', 'button:has-text("Submit")',
    'button:has-text("Send Message")', 'button:has-text("Get In Touch")',
    'button:has-text("Contact Us")',
]


async def try_fill_with_playwright(page, info: dict) -> bool:
    """Pure Playwright se form fill karo — no AI"""
    try:
        # Name fill
        for sel in NAME_SELECTORS:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.clear()
                await el.fill(info['name'])
                break

        # Email fill
        for sel in EMAIL_SELECTORS:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.clear()
                await el.fill(info['email'])
                break

        # Phone fill
        for sel in PHONE_SELECTORS:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.clear()
                await el.fill(info['phone'])
                break

        # Message fill
        for sel in MESSAGE_SELECTORS:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.clear()
                await el.fill(info['message'])
                break

        # Submit
        for sel in SUBMIT_SELECTORS:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.click()
                await page.wait_for_timeout(3000)
                return True

        return False
    except:
        return False


async def find_contact_page(page, base_url: str) -> bool:
    """FInd the contact page"""
    # Common paths try karo
    for path in CONTACT_PATHS:
        try:
            url = base_url.rstrip('/') + path
            resp = await page.goto(url, timeout=8000, wait_until='domcontentloaded')
            if resp and resp.status == 200:
                # Check karo form hai ki nahi
                form = await page.locator('form').count()
                if form > 0:
                    return True
        except:
            continue

    # Nav link dhundo
    try:
        await page.goto(base_url, timeout=10000, wait_until='domcontentloaded')
        contact_link = page.locator(
            'a:has-text("Contact"), a:has-text("contact"), '
            'a:has-text("Get In Touch"), a:has-text("Reach Us")'
        ).first
        if await contact_link.count() > 0:
            await contact_link.click()
            await page.wait_for_timeout(2000)
            return True
    except:
        pass

    return False


async def fill_with_gemini_fallback(url: str, info: dict) -> dict:
    """Gemini Flash AI fallback"""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )

        browser = Browser(
            config=BrowserConfig(
                headless=True,
                extra_chromium_args=[
                    '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
                    ]
            )
        )


        


        task = f"""
Fill contact form on {url}:
- Name: {info['name']}
- Email: {info['email']}
- Phone: {info['phone']}
- Message: {info['message']}

Find contact page, fill form by LABEL matching, submit.
Reply FORM_SUBMITTED if done, NO_FORM if no form found.
"""
        agent = Agent(task=task, llm=llm, browser=browser, max_actions_per_step=8)
        
        history = await agent.run(max_steps=10)
        result = str(history.final_result() or "")

        if "NO_FORM" in result:
            return {"status": "skipped", "message": "No contact form found"}
        else:
            return {"status": "success", "message": "Form submitted via AI ✅"}
    except Exception as e:
        return {"status": "failed", "message": str(e)[:200]}


async def fill_contact_form(url: str, info: dict) -> dict:
    """Main function — Playwright first, Gemini fallback"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            page = await browser.new_page()
            page.set_default_timeout(10000)

            # Step 1: Contact page dhundo
            found = await find_contact_page(page, url)

            if found:
                # Step 2: Form fill karo
                filled = await try_fill_with_playwright(page, info)
                await browser.close()

                if filled:
                    return {"status": "success", "message": "Form submitted via Playwright ✅"}

            await browser.close()

            # Playwright fail → Gemini fallback
            return await fill_with_gemini_fallback(url, info)

    except Exception as e:
        # Any error → Gemini fallback
        try:
            return await fill_with_gemini_fallback(url, info)
        except Exception as e2:
            return {"status": "failed", "message": str(e2)[:200]}
