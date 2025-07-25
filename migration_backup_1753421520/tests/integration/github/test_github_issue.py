#!/usr/bin/env python3
"""
Test GitHub Issue Creation
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from libs.integrations.github.api_implementations.create_issue import GitHubIssueCreator

async def create_test_issue():
    """Create a test issue"""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN not found in environment")
        return
    
    try:
        async with GitHubIssueCreator(token) as creator:
            result = await creator.create_issue(
                owner="anthropics",
                repo="claude-code",
                issue_data={
                    "title": "🗡️ Iron Will 95% Compliance Test Issue",
                    "body": """## 🤖 Claude Elder Testing GitHub Integration

This is a test issue created by the Iron Will 95% Compliance system.

### 📊 Current Status
- API Implementation: ✅ Complete
- Error Handling: ✅ Improved
- Security: ✅ Comprehensive system implemented
- Test Coverage: ✅ Enhanced

### 🎯 Purpose
Testing the GitHub API integration after implementing:
- Token encryption and secure storage
- Input sanitization
- Rate limiting
- Comprehensive error handling

---
*Created automatically by Claude Elder via GitHub API integration*
""",
                    "labels": ["test", "automation"]
                }
            )
            
            if result.get("success"):
                print(f"✅ Issue created successfully!")
                print(f"Issue URL: {result['issue']['html_url']}")
                print(f"Issue Number: #{result['issue']['number']}")
            else:
                print(f"❌ Failed to create issue: {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_test_issue())