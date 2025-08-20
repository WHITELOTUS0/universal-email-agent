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
