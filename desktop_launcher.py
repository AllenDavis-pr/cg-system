import os
import sys
import threading
import time
from pathlib import Path
import requests
from wsgiref.simple_server import make_server

# -----------------------------
# Base directories (immediate setup)
# -----------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path.home() / "AppData" / "Local" / "CGPriceSuggestor"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "db.sqlite3"
else:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR
    DB_PATH = DATA_DIR / "db.sqlite3"

CASHGEN_DIR = BASE_DIR / 'cashgen'

# Add project paths
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(CASHGEN_DIR))
sys.path.insert(0, str(CASHGEN_DIR / 'cashgen'))

os.environ["DJANGO_DB_PATH"] = str(DB_PATH)

# -----------------------------
# Set local browser path
# -----------------------------
if getattr(sys, 'frozen', False):
    # For frozen app, use a dedicated playwright directory
    PLAYWRIGHT_BROWSERS_PATH = BASE_DIR / "playwright" / ".local-browsers"
else:
    # For development
    PLAYWRIGHT_BROWSERS_PATH = BASE_DIR / "python" / "playwright" / ".local-browsers"

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(PLAYWRIGHT_BROWSERS_PATH)

# Make sure the directory exists
PLAYWRIGHT_BROWSERS_PATH.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Deferred imports and setup
# -----------------------------
def setup_environment():
    """Load environment variables - fast operation"""
    from dotenv import load_dotenv

    dotenv_path = CASHGEN_DIR / '.env'
    if not dotenv_path.exists():
        dotenv_path = BASE_DIR / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path)


def setup_django():
    """Initialize Django - only when needed"""
    import django
    from django.core.management import call_command

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cashgen.desktop_settings')
    django.setup()

    # Only run migrations if database doesn't exist or is empty
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        print("Setting up database...")
        call_command("migrate", interactive=False, verbosity=0)


def check_chromium_installed():
    """Check if Chromium is installed without importing playwright"""
    try:
        print(f"Checking for Chromium in: {PLAYWRIGHT_BROWSERS_PATH}")
        
        # Check for the chromium directory
        chromium_marker = PLAYWRIGHT_BROWSERS_PATH / "chromium"
        
        if not chromium_marker.exists():
            print(f"Chromium directory not found at: {chromium_marker}")
            return False
        
        # More thorough check - look for actual browser executable
        found_executables = []
        for item in chromium_marker.rglob("*"):
            if item.is_file() and item.name in ["chrome.exe", "chrome", "chromium.exe", "chromium", "Chromium.exe"]:
                found_executables.append(str(item))
        
        if found_executables:
            print(f"Chromium found ✅ at: {found_executables[0]}")
            return True
        else:
            print(f"Chromium directory exists but no executable found in: {chromium_marker}")
            return False
            
    except Exception as e:
        print(f"Error checking Chromium: {e}")
        return False


def install_chromium_background():
    """Install Chromium synchronously - blocking operation with live output"""
    try:
        print("=" * 60)
        print("Installing Chromium browser...")
        print("This is a one-time setup and may take 1-2 minutes.")
        print("=" * 60)
        
        from playwright.sync_api import sync_playwright
        
        # Use subprocess to install chromium
        import subprocess
        
        # Get the playwright executable path
        playwright_module = sys.modules.get('playwright')
        if playwright_module:
            playwright_path = Path(playwright_module.__file__).parent / "__main__.py"
            
            # Run installation in separate process
            env = os.environ.copy()
            env["PLAYWRIGHT_BROWSERS_PATH"] = str(PLAYWRIGHT_BROWSERS_PATH)
            
            # Force ASCII output to avoid Unicode issues
            if sys.platform == "win32":
                env["PYTHONIOENCODING"] = "utf-8"
                # Set console to UTF-8 mode
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    kernel32.SetConsoleOutputCP(65001)  # UTF-8
                except:
                    pass
            
            print(f"Installing to: {PLAYWRIGHT_BROWSERS_PATH}")
            print("Progress:")
            print("-" * 60)
            
            process = subprocess.Popen(
                [sys.executable, str(playwright_path), "install", "chromium"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'  # Replace problematic characters
            )
            
            # Track progress to avoid spam
            last_line = ""
            for line in process.stdout:
                line = line.rstrip()
                
                # Filter out progress bar lines (they start with |)
                # Only show the final percentage or non-progress lines
                if line.startswith('|'):
                    # Only print if it's 100% or every 20%
                    if '100%' in line or last_line != line:
                        # Clean up the line for better display
                        if '100%' in line:
                            # Extract just the percentage and size
                            parts = line.split('|')
                            if len(parts) >= 2:
                                info = parts[-1].strip()
                                print(f"  ✓ {info}")
                        last_line = line
                else:
                    # Print download start/complete messages
                    if line:
                        print(line)
            
            # Wait for process to complete
            return_code = process.wait()
            
            print("-" * 60)
            
            if return_code == 0:
                print("=" * 60)
                print("✅ Chromium installed successfully!")
                print("=" * 60)
                return True
            else:
                print("=" * 60)
                print(f"❌ Chromium installation error (exit code: {return_code})")
                print("=" * 60)
                return False
                
    except Exception as e:
        print("=" * 60)
        print(f"❌ Error installing Chromium: {e}")
        print("=" * 60)
        return False


def setup_playwright_background():
    """Verify Playwright setup - quick check only"""
    try:
        # Skip installation check since we already did it in main()
        from playwright.sync_api import sync_playwright
        
        print("Verifying Playwright configuration...")
        with sync_playwright() as p:
            browser_type = p.chromium
            if hasattr(browser_type, 'executable_path'):
                executable = browser_type.executable_path
                if executable and Path(executable).exists():
                    print("Playwright verified ✅")
                    return True

        print("Playwright verification complete")
        return True
        
    except Exception as e:
        print(f"Playwright verification warning: {e}")
        return False


# -----------------------------
# Fast Django server startup
# -----------------------------
def start_django_server():
    """Start Django server with minimal overhead"""
    original_cwd = os.getcwd()
    try:
        os.chdir(CASHGEN_DIR)

        # Setup Django in this thread
        setup_django()

        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application()

        # Use a more efficient server setup
        httpd = make_server('127.0.0.1', 8000, application)
        httpd.timeout = 1  # Faster response to shutdown

        print("Django server ready on http://127.0.0.1:8000")
        httpd.serve_forever()

    except Exception as e:
        print(f"Django server error: {e}")
    finally:
        os.chdir(original_cwd)


# -----------------------------
# Minimal JS API
# -----------------------------
class Api:
    def __init__(self):
        self.playwright_ready = False
        self.playwright_status = "Checking..."

    def open_analysis(self, url):
        def _open_window():
            import webview
            webview.create_window(
                title="Analysis",
                url=url,
                width=1200,
                height=800,
                resizable=True,
                min_size=(800, 600),
                js_api=self
            )

        threading.Thread(target=_open_window, daemon=True).start()
        return True

    def get_status(self):
        return {
            "playwright_ready": self.playwright_ready,
            "playwright_status": self.playwright_status
        }


# -----------------------------
# Fast server check
# -----------------------------
def wait_for_server(url="http://127.0.0.1:8000", timeout=10):
    """Quick server availability check"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code:  # Any response means server is up
                return True
        except Exception:
            time.sleep(0.2)  # Faster polling
    return False


# -----------------------------
# Main function - wait for Chromium installation
# -----------------------------
def main():
    print("CG Price Suggestor - Starting up...")

    # Setup environment immediately (fast)
    setup_environment()

    # Check and install Chromium BEFORE starting anything else
    print("Checking Chromium installation...")
    if not check_chromium_installed():
        print("Chromium not installed. Installing now...")
        print("This may take a minute - please wait...")
        success = install_chromium_background()
        if success:
            print("Chromium installation complete ✅")
        else:
            print("Warning: Chromium installation had issues, but continuing...")
    else:
        print("Chromium already installed ✅")

    # Start Django server in background
    server_thread = threading.Thread(target=start_django_server, daemon=True)
    server_thread.start()

    # Setup API
    api = Api()
    
    # Setup Playwright in background (verification only, since chromium is installed)
    def playwright_setup_wrapper():
        api.playwright_status = "Verifying Playwright..."
        result = setup_playwright_background()
        api.playwright_ready = result
        api.playwright_status = "Ready" if result else "Error - but app functional"
    
    playwright_thread = threading.Thread(
        target=playwright_setup_wrapper,
        daemon=True
    )
    playwright_thread.start()

    # Wait for server
    print("Waiting for Django server...")
    server_ready = wait_for_server(timeout=10)

    if not server_ready:
        print("Warning: Server not responding, but opening app anyway...")

    # Import webview only when needed
    import webview

    # Create main window
    webview.create_window(
        title='CG Price Suggestor',
        url='http://127.0.0.1:8000',
        width=1400,
        height=900,
        min_size=(1000, 700),
        resizable=True,
        shadow=True,
        js_api=api
    )

    print("Opening main window...")
    webview.start(debug=False)


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
    main()