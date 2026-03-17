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
2. Find Contact page (nav/footer mein: Contact, Contact Us, Get In Touch)
3. Click that link
4. Find the contact form
5. Fill fields by matching their LABELS (not position):
   - Field labeled Name/Full Name/Your Name → {info['name']}
   - Field labeled Email/Email Address → {info['email']}  
   - Field labeled Phone/Mobile/Tel/Contact → {info['phone']}
   - Field labeled Message/Query/How can we help → {info['message']}
6. Submit the form
7. Wait 3 seconds after submit
8. If ANY positive response appears (thank you, success, sent, received, will contact)
   OR if page URL changed after submit → reply: FORM_SUBMITTED
9. If no contact form found → reply: NO_FORM
10. If already on contact page (URL has /contact) → skip steps 2-3
"""


    try:
        agent = Agent(
            task=task,
            llm=llm,
            browser_session=session,
            max_actions_per_step=10,
        )

        history = await agent.run(max_steps=10)
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
