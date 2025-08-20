#!/usr/bin/env python3
"""
Universal Email Agent - Send emails across Gmail and Outlook Web
A prototype system demonstrating cross-platform web automation using LLM reasoning
"""

import json
import time
import logging
import argparse
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please install dependencies: pip install selenium webdriver-manager")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class EmailInstruction:
    """Parsed email instruction from natural language"""
    recipient: str
    subject: str
    body: str
    raw_instruction: str


class MockLLMReasoner:
    """
    Mock LLM for parsing natural language instructions and generating UI actions
    In production, this would be replaced with actual LLM API calls
    """
    
    def parse_email_instruction(self, instruction: str) -> EmailInstruction:
        """Parse natural language into structured email data"""
        logger.info(f"Parsing instruction: {instruction}")
        
        # Simple pattern matching for demo - in real implementation use LLM
        instruction_lower = instruction.lower()
        
        # Extract recipient (simplified)
        recipient = "example@example.com"  # Default
        if "to " in instruction_lower:
            words = instruction.split()
            for i, word in enumerate(words):
                if word.lower() == "to" and i + 1 < len(words):
                    next_word = words[i + 1]
                    if "@" in next_word:
                        recipient = next_word
                        break
        
        # Extract subject (simplified)
        subject = "Automated Email"
        if "about" in instruction_lower:
            words = instruction.split("about")
            if len(words) > 1:
                subject = words[1].strip().split(".")[0]
        elif "subject" in instruction_lower:
            words = instruction.split("subject")
            if len(words) > 1:
                subject = words[1].strip()
        
        # Extract body
        body = f"This email was sent automatically based on: {instruction}"
        if "saying" in instruction_lower:
            parts = instruction.split("saying")
            if len(parts) > 1:
                body = parts[1].strip().strip("'\"")
        
        parsed = EmailInstruction(
            recipient=recipient,
            subject=subject,
            body=body,
            raw_instruction=instruction
        )
        
        logger.info(f"Parsed email: {parsed}")
        return parsed
    
    def generate_ui_actions(self, provider: str, email_data: EmailInstruction) -> List[Dict]:
        """Generate provider-specific UI action steps"""
        logger.info(f"Generating UI actions for {provider}")
        
        if provider.lower() == "gmail":
            return [
                {"action": "click", "selector": "[gh='cm']", "description": "Click Compose button"},
                {"action": "type", "selector": "[name='to']", "text": email_data.recipient, "description": "Fill recipient"},
                {"action": "type", "selector": "[name='subjectbox']", "text": email_data.subject, "description": "Fill subject"},
                {"action": "type", "selector": "[role='textbox']", "text": email_data.body, "description": "Fill body"},
                {"action": "click", "selector": "[role='button'][tabindex='1']", "description": "Click Send"}
            ]
        
        elif provider.lower() == "outlook":
            return [
                {"action": "click", "selector": "[data-testid='new-mail-button']", "description": "Click New Mail"},
                {"action": "type", "selector": "[aria-label*='To']", "text": email_data.recipient, "description": "Fill recipient"},
                {"action": "type", "selector": "[aria-label*='Subject']", "text": email_data.subject, "description": "Fill subject"},
                {"action": "type", "selector": "[role='textbox'][aria-label*='body']", "text": email_data.body, "description": "Fill body"},
                {"action": "click", "selector": "[data-testid='send-button']", "description": "Click Send"}
            ]
        
        return []


class EmailProvider(ABC):
    """Abstract base class for email providers"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def navigate(self) -> bool:
        pass
    
    @abstractmethod
    def authenticate(self, username: str, password: str) -> bool:
        pass
    
    @abstractmethod
    def compose_and_send(self, email_data: EmailInstruction) -> bool:
        pass


class GmailProvider(EmailProvider):
    """Gmail Web implementation"""
    
    def get_name(self) -> str:
        return "Gmail"
    
    def navigate(self) -> bool:
        try:
            logger.info("Navigating to Gmail")
            self.driver.get("https://mail.google.com")
            time.sleep(5)
            
            # Check if we need to login
            current_url = self.driver.current_url
            if "accounts.google.com" in current_url or "signin" in current_url:
                logger.warning("Gmail requires authentication - please log in manually")
                logger.info("Current URL: " + current_url)
                # Wait for manual login or timeout
                wait_time = 60  # 60 seconds for manual login
                logger.info(f"Waiting {wait_time} seconds for manual login...")
                time.sleep(wait_time)
                
                # Check if login was successful
                if "mail.google.com" not in self.driver.current_url:
                    logger.error("Gmail login was not completed")
                    return False
            
            # Check for safety warnings
            page_source = self.driver.page_source.lower()
            if "this browser or app may not be secure" in page_source:
                logger.error("Gmail security warning detected")
                logger.info("Try using 'App passwords' or enable 'Less secure app access'")
                return False
            
            logger.info("Successfully navigated to Gmail")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to Gmail: {e}")
            return False
    
    def authenticate(self, username: str = "", password: str = "") -> bool:
        """Mock authentication - in practice would handle real auth"""
        logger.info("Mock authentication for Gmail")
        # In real implementation, handle Google OAuth or username/password
        # For demo, assume already logged in or use test account
        return True
    
    def compose_and_send(self, email_data: EmailInstruction) -> bool:
        try:
            logger.info("Composing email in Gmail")
            
            # Wait for Gmail to fully load
            time.sleep(5)
            
            # Click Compose - updated selectors for current Gmail UI
            compose_selectors = [
                "div[gh='cm']",  # Most current Gmail compose button
                "div[role='button'][gh='cm']",
                ".T-I.T-I-KE.L3",
                "[data-tooltip='Compose']",
                "div.T-I.T-I-KE.L3",
                ".z0>.L3"  # Alternative compose button selector
            ]
            
            compose_clicked = False
            for selector in compose_selectors:
                try:
                    logger.info(f"Trying compose selector: {selector}")
                    compose_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].click();", compose_btn)
                    logger.info(f"Clicked compose button with selector: {selector}")
                    compose_clicked = True
                    break
                except (TimeoutException, NoSuchElementException) as e:
                    logger.warning(f"Selector {selector} failed: {e}")
                    continue
            
            if not compose_clicked:
                logger.error("Could not find compose button")
                # Take screenshot for debugging
                self.driver.save_screenshot("/tmp/gmail_compose_error.png")
                logger.info("Screenshot saved to /tmp/gmail_compose_error.png")
                return False
            
            time.sleep(3)
            
            # Fill recipient - updated selectors
            to_selectors = [
                "input[peoplekit-id*='to']",
                "input[name='to']",
                "textarea[name='to']",
                "div[data-hovercard-id*='to'] input",
                ".wO.nr input"
            ]
            
            recipient_filled = False
            for selector in to_selectors:
                try:
                    to_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    to_field.clear()
                    to_field.send_keys(email_data.recipient)
                    logger.info(f"Filled recipient: {email_data.recipient} with selector: {selector}")
                    recipient_filled = True
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not recipient_filled:
                logger.error("Could not find recipient field")
                return False
            
            time.sleep(1)
            
            # Fill subject - updated selectors
            subject_selectors = [
                "input[name='subjectbox']",
                "input[placeholder*='Subject']",
                ".aoT input"
            ]
            
            for selector in subject_selectors:
                try:
                    subject_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    subject_field.clear()
                    subject_field.send_keys(email_data.subject)
                    logger.info(f"Filled subject: {email_data.subject}")
                    break
                except NoSuchElementException:
                    continue
            
            time.sleep(1)
            
            # Fill body - updated selectors
            body_selectors = [
                "div[role='textbox'][aria-label*='Message Body']",
                "div[role='textbox'][aria-label*='Message body']",
                "div[contenteditable='true'][role='textbox']",
                ".Am.Al.editable"
            ]
            
            for selector in body_selectors:
                try:
                    body_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    body_field.clear()
                    body_field.send_keys(email_data.body)
                    logger.info(f"Filled body: {email_data.body}")
                    break
                except NoSuchElementException:
                    continue
            
            # Send the email - ENABLED FOR TESTING
            logger.info("Attempting to send email...")
            send_selectors = [
                "div[role='button'][data-tooltip='Send']",
                "div[role='button'][aria-label*='Send']", 
                ".T-I.J-J5-Ji.aoO.v7.T-I-atl.L3",
                "[aria-label*='Send']",
                "div[data-tooltip='Send']"
            ]
            
            email_sent = False
            for selector in send_selectors:
                try:
                    send_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].click();", send_btn)
                    logger.info(f"✅ Email sent successfully using selector: {selector}")
                    email_sent = True
                    break
                except (TimeoutException, NoSuchElementException) as e:
                    logger.warning(f"Send button selector {selector} failed: {e}")
                    continue
            
            if not email_sent:
                logger.warning("Could not find send button - email may need to be sent manually")
                # Give user time to send manually if needed
                time.sleep(10)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to compose email in Gmail: {e}")
            # Take screenshot for debugging
            try:
                self.driver.save_screenshot("/tmp/gmail_error.png")
                logger.info("Error screenshot saved to /tmp/gmail_error.png")
            except:
                pass
            return False


class OutlookProvider(EmailProvider):
    """Outlook Web implementation"""
    
    def get_name(self) -> str:
        return "Outlook"
    
    def navigate(self) -> bool:
        try:
            logger.info("Navigating to Outlook")
            self.driver.get("https://outlook.live.com")
            time.sleep(5)
            
            # Check if we need to login
            current_url = self.driver.current_url
            if "login.live.com" in current_url or "signin" in current_url:
                logger.warning("Outlook requires authentication - please log in manually")
                logger.info("Current URL: " + current_url)
                # Wait for manual login or timeout
                wait_time = 60  # 60 seconds for manual login
                logger.info(f"Waiting {wait_time} seconds for manual login...")
                time.sleep(wait_time)
                
                # Check if login was successful
                if "outlook.live.com" not in self.driver.current_url:
                    logger.error("Outlook login was not completed")
                    return False
            
            # Check for bot detection
            page_source = self.driver.page_source.lower()
            if "unusual activity" in page_source or "verify" in page_source:
                logger.error("Outlook bot detection triggered")
                logger.info("Manual verification may be required")
                return False
                
            logger.info("Successfully navigated to Outlook")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to Outlook: {e}")
            return False
    
    def authenticate(self, username: str = "", password: str = "") -> bool:
        """Mock authentication"""
        logger.info("Mock authentication for Outlook")
        return True
    
    def compose_and_send(self, email_data: EmailInstruction) -> bool:
        try:
            logger.info("Composing email in Outlook")
            
            # Wait for Outlook to fully load
            time.sleep(5)
            
            # Click New Mail - updated selectors for current Outlook
            new_mail_selectors = [
                "[data-testid='new-mail-button']",
                "button[aria-label*='New mail']",
                "button[aria-label*='New message']",
                ".ms-Button--primary",
                "[data-app-section='ComposeButton']",
                "button:contains('New mail')",  # Text-based fallback
                ".o365button[title*='mail']"
            ]
            
            new_clicked = False
            for selector in new_mail_selectors:
                try:
                    logger.info(f"Trying new mail selector: {selector}")
                    if "contains" in selector:
                        # Handle text-based selector
                        new_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), 'New mail')]"))
                        )
                    else:
                        new_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    self.driver.execute_script("arguments[0].click();", new_btn)
                    logger.info(f"Clicked new mail with selector: {selector}")
                    new_clicked = True
                    break
                except (TimeoutException, NoSuchElementException) as e:
                    logger.warning(f"Selector {selector} failed: {e}")
                    continue
            
            if not new_clicked:
                logger.error("Could not find new mail button")
                # Take screenshot for debugging
                self.driver.save_screenshot("/tmp/outlook_compose_error.png")
                logger.info("Screenshot saved to /tmp/outlook_compose_error.png")
                return False
            
            time.sleep(3)
            
            # Fill recipient - updated selectors
            to_selectors = [
                "input[aria-label*='To']",
                "input[placeholder*='To']",
                "input[data-testid='to-input']",
                ".ms-BasePicker-input",
                "div[data-testid='to-picker'] input"
            ]
            
            recipient_filled = False
            for selector in to_selectors:
                try:
                    to_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    to_field.clear()
                    to_field.send_keys(email_data.recipient)
                    logger.info(f"Filled recipient: {email_data.recipient} with selector: {selector}")
                    recipient_filled = True
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not recipient_filled:
                logger.error("Could not find recipient field")
                return False
            
            time.sleep(1)
            
            # Fill subject - updated selectors
            subject_selectors = [
                "input[aria-label*='Subject']",
                "input[placeholder*='Subject']",
                "input[data-testid='subject-input']",
                ".ms-TextField-field[aria-label*='Subject']"
            ]
            
            for selector in subject_selectors:
                try:
                    subject_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    subject_field.clear()
                    subject_field.send_keys(email_data.subject)
                    logger.info(f"Filled subject: {email_data.subject}")
                    break
                except NoSuchElementException:
                    continue
            
            time.sleep(1)
            
            # Fill body - updated selectors
            body_selectors = [
                "div[role='textbox'][aria-label*='Message body']",
                "div[role='textbox'][aria-label*='message body']",
                "div[contenteditable='true'][aria-label*='body']",
                ".ms-Editor-editor",
                "div[data-testid='message-body']"
            ]
            
            for selector in body_selectors:
                try:
                    body_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    body_field.clear()
                    body_field.send_keys(email_data.body)
                    logger.info(f"Filled body: {email_data.body}")
                    break
                except NoSuchElementException:
                    continue
            
            # Send the email - ENABLED FOR TESTING
            logger.info("Attempting to send email...")
            send_selectors = [
                "button[data-testid='send-button']",
                "button[aria-label*='Send']",
                "button[title*='Send']",
                ".ms-Button--primary"
            ]
            
            email_sent = False
            for selector in send_selectors:
                try:
                    send_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].click();", send_btn)
                    logger.info(f"✅ Email sent successfully using selector: {selector}")
                    email_sent = True
                    break
                except (TimeoutException, NoSuchElementException) as e:
                    logger.warning(f"Send button selector {selector} failed: {e}")
                    continue
            
            # Try XPath fallback for text-based send button
            if not email_sent:
                try:
                    send_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Send')]"))
                    )
                    self.driver.execute_script("arguments[0].click();", send_btn)
                    logger.info("✅ Email sent successfully using XPath text selector")
                    email_sent = True
                except (TimeoutException, NoSuchElementException) as e:
                    logger.warning(f"XPath send button failed: {e}")
            
            if not email_sent:
                logger.warning("Could not find send button - email may need to be sent manually")
                # Give user time to send manually if needed
                time.sleep(10)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to compose email in Outlook: {e}")
            # Take screenshot for debugging
            try:
                self.driver.save_screenshot("/tmp/outlook_error.png")
                logger.info("Error screenshot saved to /tmp/outlook_error.png")
            except:
                pass
            return False


class UniversalEmailAgent:
    """
    Main agent class that coordinates LLM reasoning with browser automation
    """
    
    def __init__(self, headless: bool = False, use_profile: bool = True):
        self.headless = headless
        self.use_profile = use_profile
        self.driver = None
        self.llm = MockLLMReasoner()
        self.providers = {
            'gmail': GmailProvider,
            'outlook': OutlookProvider
        }
        
    def _setup_driver(self):
        """Initialize Chrome WebDriver with appropriate options for Mac M3"""
        chrome_options = Options()
        
        # Basic options
        if self.headless:
            chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        
        # More realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Use existing user profile to avoid login (optional)
        if self.use_profile:
            import os
            import tempfile
            # Create a copy of the user data for automation to avoid conflicts
            temp_user_data = os.path.join(tempfile.gettempdir(), "chrome_automation_profile")
            chrome_options.add_argument(f"--user-data-dir={temp_user_data}")
            chrome_options.add_argument("--profile-directory=Default")
            logger.info(f"Using temporary Chrome profile for automation: {temp_user_data}")
            logger.warning("Note: You may need to log in manually the first time")
        
        # Use system ChromeDriver (installed via brew) or webdriver-manager as fallback
        try:
            # Try system ChromeDriver first
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Using system ChromeDriver")
        except Exception as e:
            logger.info(f"System ChromeDriver failed ({e}), trying webdriver-manager...")
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Using webdriver-manager ChromeDriver")
            except Exception as e2:
                logger.error(f"Both ChromeDriver methods failed: {e2}")
                raise
        
        # Additional anti-detection measures
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        logger.info("Chrome WebDriver initialized with anti-detection measures")
    
    def _cleanup_driver(self):
        """Clean up WebDriver resources"""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome WebDriver closed")
    
    def execute_email_task(self, instruction: str, providers: List[str]) -> Dict[str, bool]:
        """
        Main execution method - processes instruction and sends email via specified providers
        """
        logger.info(f"Starting email task: {instruction}")
        logger.info(f"Target providers: {providers}")
        
        # Parse instruction using mock LLM
        email_data = self.llm.parse_email_instruction(instruction)
        
        results = {}
        
        try:
            self._setup_driver()
            
            for provider_name in providers:
                logger.info(f"\n--- Processing provider: {provider_name} ---")
                
                if provider_name.lower() not in self.providers:
                    logger.error(f"Unsupported provider: {provider_name}")
                    results[provider_name] = False
                    continue
                
                # Create provider instance
                provider_class = self.providers[provider_name.lower()]
                provider = provider_class(self.driver)
                
                try:
                    # Navigate to provider
                    if not provider.navigate():
                        results[provider_name] = False
                        continue
                    
                    # Authenticate (mock)
                    if not provider.authenticate():
                        results[provider_name] = False
                        continue
                    
                    # Compose and send email
                    success = provider.compose_and_send(email_data)
                    results[provider_name] = success
                    
                    if success:
                        logger.info(f"✅ Successfully processed email via {provider_name}")
                    else:
                        logger.error(f"❌ Failed to process email via {provider_name}")
                        
                except Exception as e:
                    logger.error(f"Error with provider {provider_name}: {e}")
                    results[provider_name] = False
                
                time.sleep(2)  # Brief pause between providers
        
        finally:
            self._cleanup_driver()
        
        return results
    
    def analyze_dom_structure(self, provider_name: str) -> Dict:
        """Analyze DOM structure of a provider for debugging/adaptation"""
        logger.info(f"Analyzing DOM structure for {provider_name}")
        
        try:
            self._setup_driver()
            
            provider_class = self.providers[provider_name.lower()]
            provider = provider_class(self.driver)
            
            provider.navigate()
            time.sleep(5)  # Let page load
            
            # Extract key elements
            analysis = {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'buttons': [],
                'inputs': [],
                'textareas': []
            }
            
            # Find relevant elements
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            analysis['buttons'] = [btn.get_attribute('outerHTML')[:200] for btn in buttons[:5]]
            
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            analysis['inputs'] = [inp.get_attribute('outerHTML')[:200] for inp in inputs[:5]]
            
            return analysis
            
        except Exception as e:
            logger.error(f"DOM analysis failed: {e}")
            return {}
        finally:
            self._cleanup_driver()


def main():
    parser = argparse.ArgumentParser(description='Universal Email Agent')
    parser.add_argument('instruction', help='Natural language email instruction')
    parser.add_argument('--providers', nargs='+', default=['gmail', 'outlook'], 
                       help='Email providers to use (gmail, outlook)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--analyze', action='store_true', help='Analyze DOM structure instead of sending')
    
    args = parser.parse_args()
    
    agent = UniversalEmailAgent(headless=args.headless)
    
    if args.analyze:
        for provider in args.providers:
            print(f"\n=== DOM Analysis for {provider} ===")
            analysis = agent.analyze_dom_structure(provider)
            print(json.dumps(analysis, indent=2))
    else:
        results = agent.execute_email_task(args.instruction, args.providers)
        
        print(f"\n=== Email Task Results ===")
        for provider, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{provider}: {status}")


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) == 1:
        # Demo mode
        agent = UniversalEmailAgent(headless=False)
        instruction = "Send an email to john@example.com about the project update saying 'The quarterly report is ready for review'"
        results = agent.execute_email_task(instruction, ['gmail'])
        print(results)
    else:
        main()