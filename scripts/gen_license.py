#!/usr/bin/env python
"""
License key generator for TokenSaver.
Usage:
  python gen_license.py --email user@example.com               # Pro (25 users)
  python gen_license.py --email user@example.com --enterprise   # Enterprise (999 users)
  python gen_license.py --email user@example.com --max-users 50 # Custom
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from manager.license import generate_key, save_license

def main():
    secret = os.environ.get("TOKENSAVER_LICENSE_KEY", "dev-mode")
    if secret == "dev-mode" or not secret:
        print("WARNING: TOKENSAVER_LICENSE_KEY is not set or is 'dev-mode'.")
        print("         License keys generated with 'dev-mode' are forgeable.")
        print("         Set a strong secret in production:")
        print("         export TOKENSAVER_LICENSE_KEY=your-secret-key")
        print()

    parser = argparse.ArgumentParser(description="Generate a TokenSaver license key")
    parser.add_argument("--email", required=True, help="Customer email address")
    parser.add_argument("--max-users", type=int, default=25, help="Maximum number of users (default: 25)")
    parser.add_argument("--enterprise", action="store_true", help="Enterprise tier (999 users, standalone mode)")
    parser.add_argument("--save", action="store_true", help="Save to database (only if manager is running)")

    args = parser.parse_args()

    max_users = 999 if args.enterprise else args.max_users
    tier = "Enterprise" if args.enterprise else "Pro"
    key = generate_key(args.email, max_users)

    print("=" * 55)
    print(f"  TokenSaver {tier} License Key")
    print("=" * 55)
    print(f"  Customer: {args.email}")
    print(f"  Tier:     {tier}")
    print(f"  Max Users: {max_users}")
    print(f"  Key:      {key}")
    print("=" * 55)
    print()
    print(f"  Email this key to the customer.")
    print(f"  They enter it in Settings > License on the dashboard.")

    if args.save:
        save_license(key, args.email, max_users)
        print("  (Saved to database)")

if __name__ == "__main__":
    main()
