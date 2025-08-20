# Troubleshooting Guide

## Common Issues and Solutions

### 1. Gmail "This browser or app may not be secure" Error

**Problem**: Gmail blocks the automated browser for security reasons.

**Solutions**:

1. **Use App Passwords** (Recommended):

   - Go to Google Account settings
   - Enable 2-factor authentication
   - Generate an app password for the email agent
   - Use the app password instead of regular password

2. **Enable Less Secure App Access**:

   - Go to Google Account → Security
   - Turn on "Less secure app access"
   - ⚠️ Not recommended for production use

3. **Use OAuth 2.0**:
   - Implement proper OAuth 2.0 flow
   - Get API credentials from Google Cloud Console

### 2. Outlook Login Termination/Bot Detection

**Problem**: Outlook detects automated browser and terminates session.

**Solutions**:

1. **Use Existing Profile**:

   ```python
   agent = UniversalEmailAgent(headless=False, use_profile=True)
   ```

2. **Manual Login**:

   - Run in non-headless mode
   - Log in manually when prompted
   - The agent will wait 60 seconds for manual login

3. **Use Microsoft Graph API**:
   - Implement proper API integration instead of browser automation

### 3. ChromeDriver Issues

**Problem**: ChromeDriver not found or version mismatch.

**Solutions**:

1. **Automatic Installation** (Included):

   ```bash
   pip install webdriver-manager
   ```

2. **Manual Installation**:

   ```bash
   brew install chromedriver
   ```

3. **Version Mismatch**:
   - Check Chrome version: `chrome://version/`
   - Download matching ChromeDriver from https://chromedriver.chromium.org/

### 4. Selector Issues (Elements Not Found)

**Problem**: Email UI elements not found due to updated selectors.

**Solutions**:

1. **Use DOM Analysis**:

   ```python
   python email_agent.py --analyze --providers gmail
   ```

2. **Update Selectors**:

   - Inspect element in browser
   - Update selectors in provider classes

3. **Take Screenshots**:
   - Error screenshots are saved to `/tmp/`
   - Use them to debug selector issues

### 5. Authentication Timeout

**Problem**: Manual login takes too long.

**Solutions**:

1. **Increase Timeout**:

   ```python
   # In navigate() method, change:
   wait_time = 120  # Increase from 60 to 120 seconds
   ```

2. **Pre-authenticate**:
   - Log into Gmail/Outlook in regular Chrome first
   - Use profile option to reuse session

### 6. Network/Firewall Issues

**Problem**: Corporate firewall blocks automation.

**Solutions**:

1. **Proxy Support**:

   ```python
   chrome_options.add_argument("--proxy-server=your-proxy:port")
   ```

2. **VPN/Network Change**:
   - Try different network
   - Use personal device for testing

## Testing Workflow

1. **Test Dependencies**:

   ```bash
   python -c "from selenium import webdriver; print('Selenium OK')"
   python -c "from webdriver_manager.chrome import ChromeDriverManager; print('WebDriver Manager OK')"
   ```

2. **Test Basic Browser**:

   ```bash
   python -c "
   from selenium import webdriver
   from webdriver_manager.chrome import ChromeDriverManager
   from selenium.webdriver.chrome.service import Service
   driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
   driver.get('https://google.com')
   print('Browser test OK')
   driver.quit()
   "
   ```

3. **Test Components**:

   ```bash
   python test_agent.py
   ```

4. **Test with Single Provider**:

   ```bash
   # Test Gmail only
   python email_agent.py "Send email to test@example.com about test" --providers gmail

   # Test Outlook only
   python email_agent.py "Send email to test@example.com about test" --providers outlook
   ```

## Debug Mode

Run with detailed logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Or modify the logging level in email_agent.py:
logging.basicConfig(level=logging.DEBUG)
```

## Manual Override

For testing, you can manually send emails by uncommenting the send button click in the provider code:

```python
# In GmailProvider.compose_and_send():
# Uncomment these lines:
# send_btn = self.driver.find_element(By.CSS_SELECTOR, "div[role='button'][data-tooltip='Send']")
# send_btn.click()
```

⚠️ **Warning**: Only do this in a test environment with your own email addresses.

## Contact Support

If issues persist:

1. Check the logs in `email_agent.log`
2. Review screenshots in `/tmp/`
3. Ensure you're using the latest Chrome browser
4. Try running in non-headless mode to see what's happening

Remember: This is a prototype for educational purposes. For production use, consider using official email APIs instead of browser automation.
