"""
Capture 4 professional working model screenshots for Umbrella technical report.
Resolution: 1920x1080, PNG format.
"""
import os
import sys
import time
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = ROOT / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

def wait_for_backend_ready(url="http://127.0.0.1:8000/api/health", max_tries=20):
    import urllib.request
    for i in range(max_tries):
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    print("Backend is healthy.")
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def save_dual(page, filename):
    path1 = SCREENSHOTS_DIR / filename
    path2 = ROOT / filename
    page.screenshot(path=str(path1), full_page=False)
    page.screenshot(path=str(path2), full_page=False)
    print(f"Captured: {filename} -> {path1} and {path2}")

def capture_all():
    if not wait_for_backend_ready():
        print("Backend not available!")
        sys.exit(1)

    print("Launching Chromium at 1920x1080...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--window-size=1920,1080",
                "--hide-scrollbars",
                "--disable-background-timer-throttling",
                "--enable-font-antialiasing",
            ]
        )

        # =========================================================================
        # SCREENSHOT 3: Conversational Context
        # =========================================================================
        print("\n--- Generating Screenshot 3: Conversational Context ---")
        context3 = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0,
        )
        page3 = context3.new_page()
        page3.set_default_timeout(25000)

        session_id_3 = f"report_session_03_{int(time.time())}"
        page3.add_init_script(f"""
            localStorage.setItem('umbrella_session_id', '{session_id_3}');
            localStorage.setItem('umbrella_demo_mode', 'false');
            localStorage.setItem('umbrella_unit', '°C');
        """)
        page3.goto("http://127.0.0.1:8000")
        page3.wait_for_selector("text=umbrella.", timeout=15000)
        time.sleep(1)

        composer3 = page3.locator("textarea").first
        send_btn3 = page3.locator("button[title='Send message']").first
        
        composer3.fill("I have college from 9 AM to 4 PM in Pune")
        time.sleep(0.5)
        send_btn3.click()
        page3.wait_for_selector("text=College Plan", timeout=15000)
        page3.wait_for_selector("text=09:00 – 16:00", timeout=15000)
        time.sleep(2)

        # Follow-up message: What if I leave at 5 PM instead?
        composer3.fill("What if I leave at 5 PM instead?")
        time.sleep(0.5)
        send_btn3.click()
        
        # Wait for the updated college response
        page3.wait_for_selector("text=09:00 – 17:00", timeout=15000)
        time.sleep(2.5)

        # Scroll so the conversational follow-up prompt and its response card are framed
        page3.evaluate("""
            const bubbles = Array.from(document.querySelectorAll('div')).filter(el => el.textContent && el.textContent.includes('What if I leave at 5 PM instead?'));
            if (bubbles.length > 0) {
                bubbles[0].scrollIntoView({ behavior: 'instant', block: 'start' });
            }
        """)
        time.sleep(1)

        save_dual(page3, "03-conversational-followup.png")
        context3.close()

        # =========================================================================
        # SCREENSHOT 4: Adaptive Plan Comparison
        # =========================================================================
        print("\n--- Generating Screenshot 4: Adaptive Plan Comparison ---")
        context4 = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0,
        )
        page4 = context4.new_page()
        page4.set_default_timeout(25000)

        session_id_4 = f"report_session_04_{int(time.time())}"
        page4.add_init_script(f"""
            localStorage.setItem('umbrella_session_id', '{session_id_4}');
            localStorage.setItem('umbrella_demo_mode', 'true');
            localStorage.setItem('umbrella_demo_scenario', 'Moderate');
            localStorage.setItem('umbrella_unit', '°C');
        """)
        page4.goto("http://127.0.0.1:8000")
        page4.wait_for_selector("text=umbrella.", timeout=15000)
        time.sleep(1)

        composer4 = page4.locator("textarea").first
        send_btn4 = page4.locator("button[title='Send message']").first

        composer4.fill("I have college from 3 PM to 6 PM in Pune")
        time.sleep(0.5)
        send_btn4.click()
        page4.wait_for_selector("text=College Plan", timeout=15000)
        page4.wait_for_selector("text=15:00 – 18:00", timeout=15000)
        time.sleep(2)

        # Send: Can you find a better time?
        composer4.fill("Can you find a better time?")
        time.sleep(0.5)
        send_btn4.click()

        # Wait for Adaptive Plan Comparison card
        page4.wait_for_selector("text=Lower-Risk Window Suggested", timeout=15000)
        page4.wait_for_selector("text=Original Plan", timeout=15000)
        page4.wait_for_selector("text=Suggested Alternative", timeout=15000)
        time.sleep(2)

        # Scroll so the prompt 'Can you find a better time?' and the full comparison card fit cleanly
        page4.evaluate("""
            const userPrompt = Array.from(document.querySelectorAll('div')).find(el => el.textContent === 'Can you find a better time?');
            if (userPrompt) {
                const top = userPrompt.getBoundingClientRect().top + window.pageYOffset - 80;
                window.scrollTo({ top: top, behavior: 'instant' });
            }
        """)
        time.sleep(1)

        save_dual(page4, "04-adaptive-plan-comparison.png")

        # =========================================================================
        # SCREENSHOT 5: Agent Activity
        # =========================================================================
        print("\n--- Generating Screenshot 5: Agent Activity ---")
        trace_button = page4.locator("button:has-text('Agent Activity')").last
        trace_button.scroll_into_view_if_needed()
        time.sleep(0.5)
        trace_button.click()

        # Wait for trace steps
        page4.wait_for_selector("text=Goal interpreted", timeout=10000)
        page4.wait_for_selector("text=Alternatives compared", timeout=10000)
        time.sleep(1)

        # Click step 5 (Alternatives compared) to expand inputs/outputs
        step_btn = page4.locator("button:has-text('Alternatives compared')").last
        step_btn.click()
        time.sleep(1)

        # Scroll so the entire Agent Activity panel with Specialist Roles is in view
        page4.evaluate("""
            const trace = Array.from(document.querySelectorAll('button')).filter(el => el.textContent && el.textContent.includes('Agent Activity')).pop();
            if (trace) {
                const y = trace.getBoundingClientRect().top + window.pageYOffset - 80;
                window.scrollTo({ top: y, behavior: 'instant' });
            }
        """)
        time.sleep(1)

        save_dual(page4, "05-agent-activity.png")
        context4.close()

        # =========================================================================
        # SCREENSHOT 6: Location Switching
        # =========================================================================
        print("\n--- Generating Screenshot 6: Location Switching ---")
        context6 = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0,
        )
        page6 = context6.new_page()
        page6.set_default_timeout(25000)

        session_id_6 = f"report_session_06_{int(time.time())}"
        page6.add_init_script(f"""
            localStorage.setItem('umbrella_session_id', '{session_id_6}');
            localStorage.setItem('umbrella_demo_mode', 'false');
            localStorage.setItem('umbrella_unit', '°C');
        """)
        page6.goto("http://127.0.0.1:8000")
        page6.wait_for_selector("text=umbrella.", timeout=15000)
        time.sleep(1)

        composer6 = page6.locator("textarea").first
        send_btn6 = page6.locator("button[title='Send message']").first

        # Initial plan in Pune
        composer6.fill("I have college from 9 AM to 4 PM in Pune")
        time.sleep(0.5)
        send_btn6.click()
        page6.wait_for_selector("text=College Plan", timeout=15000)
        time.sleep(2)

        # Open Location Indicator popover
        loc_btn = page6.locator("button[aria-haspopup='dialog']").first
        loc_btn.click()
        page6.wait_for_selector("input[placeholder*='Search city']", timeout=5000)
        time.sleep(0.5)

        # Search for Mumbai
        search_input = page6.locator("input[placeholder*='Search city']").first
        search_input.fill("Mumbai")
        time.sleep(1.0)

        # Click Mumbai from results
        mumbai_option = page6.locator("button:has-text('Mumbai')").first
        page6.wait_for_selector("button:has-text('Mumbai')", timeout=8000)
        time.sleep(0.5)
        mumbai_option.click()

        # Wait for recalculated forecast message in Mumbai
        page6.wait_for_selector("text=Location updated to Mumbai", timeout=15000)
        page6.wait_for_selector("button:has-text('Mumbai, Maharashtra, India')", timeout=10000)
        time.sleep(2.5)

        # Scroll so the updated location header and the recalculation message are visible
        page6.evaluate("""
            const items = document.querySelectorAll('.chat-message-item, [class*="ChatMessageItem"], div.group');
            if (items.length > 0) {
                items[items.length - 1].scrollIntoView({ behavior: 'instant', block: 'end' });
            }
        """)
        time.sleep(1)

        save_dual(page6, "06-location-switching.png")
        context6.close()

        browser.close()
        print("\nAll 4 screenshots captured successfully!")

if __name__ == "__main__":
    capture_all()
