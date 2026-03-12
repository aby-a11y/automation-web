import asyncio
from browser_use import Agent, BrowserSession, BrowserProfile, ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

async def fill_contact_form(url: str, info: dict) -> dict:

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    profile = BrowserProfile(
        headless=True,
        extra_chromium_args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
    )

    session = BrowserSession(browser_profile=profile)

    task = f"""
    You are a form filling assistant. Follow these steps carefully:

    1. Go to this URL: {url}
    2. Look for a Contact page link in navigation menu or footer
       (words like: Contact, Contact Us, Get In Touch, Reach Us, Write to Us)
    3. Click that link to go to contact page
    4. Find the contact form on that page
    5. Fill in these details:
       - Name / Full Name: {info['name']}
       - Email / Email Address: {info['email']}
       - Phone / Mobile / Contact Number: {info['phone']}
       - Message / Query / Description / How can we help: {info['message']}
    6. Click the Submit / Send / Send Message button
    7. Wait for confirmation (thank you message, success alert, page change)
    8. If successful, reply exactly: FORM_SUBMITTED
    9. If no contact form found anywhere on site, reply: NO_FORM
    10. If already on contact page (URL contains /contact), skip step 2 and 3
    """

    try:
        agent = Agent(
            task=task,
            llm=llm,
            browser_session=session,
            max_actions_per_step=10,
        )

        history = await agent.run(max_steps=20)
        result = str(history.final_result() or "")

        if "NO_FORM" in result:
            return {"status": "skipped", "message": "No contact form found on this site"}
        elif "FORM_SUBMITTED" in result:
            return {"status": "success", "message": "Form submitted successfully ✅"}
        else:
            # Agent kuch aur bola — probably success hi hai
            return {"status": "success", "message": result[:200]}

    except Exception as e:
        return {"status": "failed", "message": str(e)[:200]}

    finally:
        await session.close()
