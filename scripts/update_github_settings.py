#!/usr/bin/env python3
"""
Script to update GitHub repository settings via API.
Run this to update topics and make tokensaver public.
"""

import requests
import json
import os

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_URL = "https://api.github.com"

def update_repo_topics(owner, repo, topics):
    """Update repository topics"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/topics"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.mercy-preview+json"
    }
    data = {"names": topics}
    
    response = requests.put(url, headers=headers, json=data)
    return response.status_code == 200, response.json()

def update_repo_visibility(owner, repo, private=False):
    """Update repository visibility"""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"private": private}
    
    response = requests.patch(url, headers=headers, json=data)
    return response.status_code == 200, response.json()

# TokenSaver topics
tokensaver_topics = [
    "llm",
    "cost-governance",
    "rate-limiting",
    "prompt-caching",
    "api-proxy",
    "openai",
    "budget-management",
    "fastapi",
    "python",
    "self-hosted"
]

# PROMPTER topics
prompter_topics = [
    "prompt-engineering",
    "ai-tools",
    "llm",
    "prompt-optimization",
    "gemini",
    "nextjs",
    "react",
    "typescript"
]

# Kunal topics
kunal_topics = [
    "ai-studio",
    "nextjs",
    "gemini-api",
    "typescript",
    "react",
    "javascript"
]

if __name__ == "__main__":
    print("🚀 Updating GitHub repositories...\n")
    
    # Update TokenSaver
    print("1️⃣  Updating TokenSaver...")
    print("   - Setting topics:", tokensaver_topics)
    success, response = update_repo_topics("kunalmavani01-boop", "tokensaver", tokensaver_topics)
    if success:
        print("   ✅ Topics updated!")
    else:
        print(f"   ❌ Error: {response}")
    
    print("   - Making repository public...")
    success, response = update_repo_visibility("kunalmavani01-boop", "tokensaver", private=False)
    if success:
        print("   ✅ Repository is now public!")
    else:
        print(f"   ❌ Error: {response}")
    
    # Update PROMPTER
    print("\n2️⃣  Updating PROMPTER...")
    print("   - Setting topics:", prompter_topics)
    success, response = update_repo_topics("kunalmavani01-boop", "PROMPTER", prompter_topics)
    if success:
        print("   ✅ Topics updated!")
    else:
        print(f"   ❌ Error: {response}")
    
    # Update Kunal
    print("\n3️⃣  Updating Kunal...")
    print("   - Setting topics:", kunal_topics)
    success, response = update_repo_topics("kunalmavani01-boop", "kunal", kunal_topics)
    if success:
        print("   ✅ Topics updated!")
    else:
        print(f"   ❌ Error: {response}")
    
    print("\n✨ All updates complete!")
