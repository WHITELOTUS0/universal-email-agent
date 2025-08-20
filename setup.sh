echo "Setting up Universal Email Agent for Mac M3..."


# Install Python requirements
pip install -r requirements.txt

# Install ChromeDriver (for Mac M3)
if ! command -v chromedriver &> /dev/null; then
    echo "Installing ChromeDriver..."
    
    # Method 1: Using Homebrew (recommended)
    if command -v brew &> /dev/null; then
        brew install chromedriver
    else
        echo "Homebrew not found. Please install ChromeDriver manually:"
        echo "1. Download from: https://chromedriver.chromium.org/"
        echo "2. Choose the version matching your Chrome browser"
        echo "3. Download the Mac ARM64 version for M3"
        echo "4. Extract and move to /usr/local/bin/"
        echo "5. Run: xattr -d com.apple.quarantine /usr/local/bin/chromedriver"
    fi
fi

# Verify installation
python -c "from selenium import webdriver; print('Selenium installed successfully')"

echo "Setup complete!"
echo ""
echo "Usage examples:"
echo "python email_agent.py 'Send email to alice@example.com about meeting tomorrow'"
echo "python email_agent.py 'Email bob@company.com saying Hello from automation' --providers gmail"
echo "python email_agent.py 'Send status update to team@company.com' --headless --providers outlook"

# Test script
cat > test_agent.py << 'EOF'
#!/usr/bin/env python3
"""
Quick test script for the Email Agent
"""

from email_agent import UniversalEmailAgent

def test_mock_parsing():
    """Test the mock LLM parsing functionality"""
    agent = UniversalEmailAgent(headless=True)
    
    test_instructions = [
        "Send an email to alice@company.com about the quarterly report saying 'Please review the attached document'",
        "Email bob@example.com about lunch meeting",
        "Send notification to team@startup.com saying 'Deploy completed successfully'"
    ]
    
    for instruction in test_instructions:
        email_data = agent.llm.parse_email_instruction(instruction)
        print(f"\nInstruction: {instruction}")
        print(f"Parsed: {email_data}")

def test_ui_actions():
    """Test UI action generation"""
    agent = UniversalEmailAgent()
    from email_agent import EmailInstruction
    
    email_data = EmailInstruction(
        recipient="test@example.com",
        subject="Test Subject",
        body="Test Body",
        raw_instruction="test"
    )
    
    for provider in ['gmail', 'outlook']:
        actions = agent.llm.generate_ui_actions(provider, email_data)
        print(f"\n{provider} actions:")
        for action in actions:
            print(f"  - {action}")

if __name__ == "__main__":
    print("Testing Email Agent Components...")
    test_mock_parsing()
    test_ui_actions()
    print("\nComponent tests completed!")
EOF

chmod +x test_agent.py

echo "Created test_agent.py for component testing"