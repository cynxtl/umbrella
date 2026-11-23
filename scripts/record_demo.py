"""Record clean, silent product demonstration video for Umbrella at 1920x1080 (H.264 MP4)."""
import os
import sys
import time
import pathlib
import subprocess
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECORDINGS_DIR = ROOT / "recordings"
RAW_DIR = RECORDINGS_DIR / "raw_capture"
FINAL_VIDEO = RECORDINGS_DIR / "umbrella-demo.mp4"

def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def smooth_move(page, start_x, start_y, end_x, end_y, steps=28):
    for i in range(1, steps + 1):
        t = i / steps
        ease = t * t * (3.0 - 2.0 * t)
        curr_x = start_x + (end_x - start_x) * ease
        curr_y = start_y + (end_y - start_y) * ease
        page.mouse.move(curr_x, curr_y)
        time.sleep(0.016)
    return end_x, end_y

def inject_cursor(page):
    page.evaluate("""
    (() => {
      if (document.getElementById('demo-virtual-cursor')) return;

      const cursor = document.createElement('div');
      cursor.id = 'demo-virtual-cursor';
      cursor.style.position = 'fixed';
      cursor.style.top = '0';
      cursor.style.left = '0';
      cursor.style.zIndex = '9999999';
      cursor.style.pointerEvents = 'none';
      cursor.style.transform = 'translate(960px, 540px)';
      cursor.style.transition = 'opacity 0.2s';
      cursor.innerHTML = `
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 2px 5px rgba(0,0,0,0.6));">
          <path d="M5.5 3.5L18.5 11.5L12 13.5L9.5 20L5.5 3.5Z" fill="#FFFFFF" stroke="#000000" stroke-width="1.6" stroke-linejoin="round"/>
        </svg>
      `;
      document.body.appendChild(cursor);

      const ripple = document.createElement('div');
      ripple.id = 'demo-virtual-ripple';
      ripple.style.position = 'fixed';
      ripple.style.width = '24px';
      ripple.style.height = '24px';
      ripple.style.borderRadius = '50%';
      ripple.style.border = '2px solid rgba(255, 255, 255, 0.7)';
      ripple.style.backgroundColor = 'rgba(255, 255, 255, 0.15)';
      ripple.style.zIndex = '9999998';
      ripple.style.pointerEvents = 'none';
      ripple.style.opacity = '0';
      ripple.style.transform = 'translate(-50%, -50%) scale(0.5)';
      ripple.style.transition = 'transform 0.25s ease-out, opacity 0.25s ease-out';
      document.body.appendChild(ripple);

      window.addEventListener('mousemove', (e) => {
        cursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
      });

      window.addEventListener('mousedown', (e) => {
        ripple.style.left = `${e.clientX + 4}px`;
        ripple.style.top = `${e.clientY + 4}px`;
        ripple.style.opacity = '1';
        ripple.style.transform = 'translate(-50%, -50%) scale(1.4)';
        setTimeout(() => {
          ripple.style.opacity = '0';
          ripple.style.transform = 'translate(-50%, -50%) scale(0.5)';
        }, 250);
      });
    })();
    """)

def record_demo():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Launching Chromium at 1920x1080 ===")
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
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(RAW_DIR),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        # Step 1: Landing Page
        print("[1/7] Navigating to landing page...")
        page.goto("http://127.0.0.1:8000")
        page.wait_for_load_state("networkidle")
        inject_cursor(page)

        # Initial mouse position
        mx, my = 960, 540
        page.mouse.move(mx, my)

        # Showcase landing page (greeting, suggestion chips, composer)
        print("  Showcasing landing view (4.5s)...")
        time.sleep(4.5)

        # Step 2: Weather Query & Location Selection
        print("[2/7] Submitting initial weather query: 'Will I need an umbrella tomorrow?'...")
        composer = page.locator("textarea")
        box = composer.bounding_box()
        if box:
            target_x = box["x"] + box["width"] * 0.3
            target_y = box["y"] + box["height"] * 0.5
            mx, my = smooth_move(page, mx, my, target_x, target_y, steps=25)
            page.mouse.click(mx, my)
            time.sleep(0.3)

            # Type query naturally
            page.keyboard.type("Will I need an umbrella tomorrow?", delay=55)
            time.sleep(0.6)

            # Click send button
            send_btn = page.locator("button[title='Send message'], button:has-text('Send')").first
            btn_box = send_btn.bounding_box()
            if btn_box:
                bx = btn_box["x"] + btn_box["width"] / 2
                by = btn_box["y"] + btn_box["height"] / 2
                mx, my = smooth_move(page, mx, my, bx, by, steps=20)
                page.mouse.click(mx, my)

        # Wait for assistant response asking for city
        page.wait_for_selector("text=Please choose your location", timeout=12000)
        time.sleep(2.5)

        # Select Pune using the header location indicator
        print("  Selecting Pune from header location indicator...")
        loc_btn = page.locator("button[aria-haspopup='dialog']").first
        loc_box = loc_btn.bounding_box()
        if loc_box:
            lx = loc_box["x"] + loc_box["width"] / 2
            ly = loc_box["y"] + loc_box["height"] / 2
            mx, my = smooth_move(page, mx, my, lx, ly, steps=25)
            page.mouse.click(mx, my)
            time.sleep(0.8)

            # Search Pune
            search_input = page.locator("input[placeholder*='Search city']").first
            if search_input.is_visible():
                si_box = search_input.bounding_box()
                if si_box:
                    sx = si_box["x"] + si_box["width"] * 0.3
                    sy = si_box["y"] + si_box["height"] / 2
                    mx, my = smooth_move(page, mx, my, sx, sy, steps=15)
                    page.mouse.click(mx, my)
                    page.keyboard.type("Pune", delay=60)
                    time.sleep(0.8)

            # Click Pune option from results
            pune_option = page.locator("button:has-text('Pune')").first
            p_box = pune_option.bounding_box()
            if p_box:
                px = p_box["x"] + p_box["width"] / 2
                py = p_box["y"] + p_box["height"] / 2
                mx, my = smooth_move(page, mx, my, px, py, steps=20)
                page.mouse.click(mx, my)
                time.sleep(1.0)

        # Re-send prompt now that Pune is confirmed
        print("  Re-sending weather query with Pune confirmed...")
        box = composer.bounding_box()
        if box:
            target_x = box["x"] + box["width"] * 0.3
            target_y = box["y"] + box["height"] * 0.5
            mx, my = smooth_move(page, mx, my, target_x, target_y, steps=25)
            page.mouse.click(mx, my)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type("Will I need an umbrella tomorrow?", delay=55)
            time.sleep(0.5)

            btn_box = send_btn.bounding_box()
            if btn_box:
                bx = btn_box["x"] + btn_box["width"] / 2
                by = btn_box["y"] + btn_box["height"] / 2
                mx, my = smooth_move(page, mx, my, bx, by, steps=20)
                page.mouse.click(mx, my)

        # Wait for Weather recommendation to appear
        page.wait_for_selector("div:has-text('Pune, Maharashtra, India')", timeout=15000)
        print("  Weather recommendation displayed.")
        time.sleep(4.5)

        # Step 3: Conversational Follow-Up (Activity Planning)
        print("[3/7] Submitting activity follow-up: 'I have college from 9 AM to 4 PM.'...")
        box = composer.bounding_box()
        if box:
            target_x = box["x"] + box["width"] * 0.3
            target_y = box["y"] + box["height"] * 0.5
            mx, my = smooth_move(page, mx, my, target_x, target_y, steps=25)
            page.mouse.click(mx, my)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type("I have college from 9 AM to 4 PM.", delay=55)
            time.sleep(0.6)

            btn_box = send_btn.bounding_box()
            if btn_box:
                bx = btn_box["x"] + btn_box["width"] / 2
                by = btn_box["y"] + btn_box["height"] / 2
                mx, my = smooth_move(page, mx, my, bx, by, steps=20)
                page.mouse.click(mx, my)

        page.wait_for_selector("text=College Plan", timeout=15000)
        print("  College activity plan displayed.")
        time.sleep(5.0)

        # Step 4: Plan Comparison
        print("[4/7] Requesting schedule comparison: 'Can you find a better time?'...")
        box = composer.bounding_box()
        if box:
            target_x = box["x"] + box["width"] * 0.3
            target_y = box["y"] + box["height"] * 0.5
            mx, my = smooth_move(page, mx, my, target_x, target_y, steps=25)
            page.mouse.click(mx, my)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type("Can you find a better time?", delay=55)
            time.sleep(0.6)

            btn_box = send_btn.bounding_box()
            if btn_box:
                bx = btn_box["x"] + btn_box["width"] / 2
                by = btn_box["y"] + btn_box["height"] / 2
                mx, my = smooth_move(page, mx, my, bx, by, steps=20)
                page.mouse.click(mx, my)

        # Wait for comparison response
        print("  Waiting for plan comparison card...")
        page.wait_for_selector("text=Original Plan", timeout=15000)
        print("  Adaptive comparison card displayed.")
        time.sleep(5.5)

        # Step 5: Agent Activity Trace
        print("[5/7] Expanding Agent Activity execution trace...")
        trace_btn = page.locator("button:has-text('Agent Activity')").last
        trace_btn.scroll_into_view_if_needed()
        time.sleep(0.5)
        t_box = trace_btn.bounding_box()
        if t_box:
            tx = t_box["x"] + t_box["width"] / 2
            ty = t_box["y"] + t_box["height"] / 2
            mx, my = smooth_move(page, mx, my, tx, ty, steps=25)
            page.mouse.click(mx, my)
            print("  Trace expanded. Displaying steps and specialist roles (6.0s)...")
            time.sleep(6.0)

        # Step 6: Location Switching to Mumbai
        print("[6/7] Switching location to Mumbai in header...")
        loc_btn = page.locator("button[aria-haspopup='dialog']").first
        loc_btn.scroll_into_view_if_needed()
        time.sleep(0.5)
        loc_box = loc_btn.bounding_box()
        if loc_box:
            lx = loc_box["x"] + loc_box["width"] / 2
            ly = loc_box["y"] + loc_box["height"] / 2
            mx, my = smooth_move(page, mx, my, lx, ly, steps=25)
            page.mouse.click(mx, my)
            time.sleep(0.8)

            search_input = page.locator("input[placeholder*='Search city']").first
            if search_input.is_visible():
                si_box = search_input.bounding_box()
                if si_box:
                    sx = si_box["x"] + si_box["width"] * 0.3
                    sy = si_box["y"] + si_box["height"] / 2
                    mx, my = smooth_move(page, mx, my, sx, sy, steps=15)
                    page.mouse.click(mx, my)
                    page.keyboard.type("Mumbai", delay=60)
                    time.sleep(0.8)

            mumbai_opt = page.locator("button:has-text('Mumbai')").first
            m_box = mumbai_opt.bounding_box()
            if m_box:
                px = m_box["x"] + m_box["width"] / 2
                py = m_box["y"] + m_box["height"] / 2
                mx, my = smooth_move(page, mx, my, px, py, steps=20)
                page.mouse.click(mx, my)

        # Wait for recalculated Mumbai message
        page.wait_for_selector("text=Location updated to Mumbai", timeout=15000)
        print("  Mumbai plan recalculated.")
        time.sleep(6.0)

        # Step 7: Clean End Pause
        print("[7/7] Finishing on clean conversational interface...")
        mx, my = smooth_move(page, mx, my, 1600, 920, steps=30)
        time.sleep(4.5)

        # Close context and finish screencast
        print("Closing browser context to finalize raw video...")
        context.close()
        raw_video_path = page.video.path()
        print(f"Raw video saved at: {raw_video_path}")
        browser.close()

    # Transcode with FFmpeg to H.264 MP4 at 1920x1080 CRF 17
    ffmpeg_exe = get_ffmpeg_path()
    print(f"=== Encoding to final H.264 MP4 using {ffmpeg_exe} ===")
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(raw_video_path),
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-an",
        str(FINAL_VIDEO),
    ]
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg encoding error:")
        print(result.stderr)
        sys.exit(1)

    print(f"=== SUCCESS: Video created at {FINAL_VIDEO} ===")
    
    # Probe final output properties
    probe_cmd = [ffmpeg_exe, "-i", str(FINAL_VIDEO)]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
    for line in probe_res.stderr.splitlines():
        if "Duration" in line or "Stream #0:0" in line:
            print(f"  {line.strip()}")

if __name__ == "__main__":
    record_demo()
