#!/usr/bin/env python3
"""CLI utility to test GitSentry Webhook Receiver with HMAC signatures.

Usage:
    python scripts/test_webhook.py --event ping
    python scripts/test_webhook.py --event pull_request --action opened
    python scripts/test_webhook.py --event issue_comment --action created
    python scripts/test_webhook.py --event pull_request --invalid-signature
"""

import argparse
import json
import os
import sys
from pathlib import Path
import uuid
import httpx

# Ensure project root is in sys.path when script is executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.crypto import generate_github_signature


def build_ping_payload() -> dict:
    return {
        "zen": "Approachable is better than simple.",
        "hook_id": 12345678,
        "hook": {
            "type": "App",
            "id": 12345678,
            "name": "web",
            "active": True,
            "events": ["pull_request", "issue_comment"],
        },
        "repository": {
            "id": 98765432,
            "name": "gitsentry-demo-repo",
            "full_name": "octocat/gitsentry-demo-repo",
            "private": False,
            "owner": {"login": "octocat", "id": 1},
        },
        "sender": {"login": "octocat", "id": 1},
    }


def build_pr_payload(action: str = "opened") -> dict:
    return {
        "action": action,
        "number": 42,
        "pull_request": {
            "id": 10042,
            "number": 42,
            "state": "open",
            "title": "Add staging health check route",
            "body": "Adds an unauthenticated /health route on staging for synthetic monitors.",
            "user": {
                "login": "dev-alice",
                "id": 54321,
                "type": "User",
            },
            "head": {
                "sha": "a1b2c3d4e5f678901234567890abcdef12345678",
                "ref": "feature/health-route",
            },
            "base": {
                "sha": "f0e1d2c3b4a5968778695041322110abcdef4321",
                "ref": "main",
            },
            "diff_url": "https://github.com/octocat/gitsentry-demo-repo/pull/42.diff",
            "html_url": "https://github.com/octocat/gitsentry-demo-repo/pull/42",
        },
        "repository": {
            "id": 98765432,
            "name": "gitsentry-demo-repo",
            "full_name": "octocat/gitsentry-demo-repo",
            "private": False,
            "owner": {"login": "octocat", "id": 1},
        },
        "sender": {
            "login": "dev-alice",
            "id": 54321,
            "type": "User",
        },
        "installation": {
            "id": 999888,
        },
    }


def build_comment_payload(action: str = "created") -> dict:
    return {
        "action": action,
        "issue": {
            "number": 42,
            "id": 10042,
            "title": "Add staging health check route",
            "pull_request": {
                "url": "https://api.github.com/repos/octocat/gitsentry-demo-repo/pulls/42",
                "html_url": "https://github.com/octocat/gitsentry-demo-repo/pull/42",
            },
            "user": {"login": "dev-alice", "id": 54321},
        },
        "comment": {
            "id": 778899,
            "body": "@gitsentry This is approved per security exemption #102 for staging monitor checks only.",
            "user": {"login": "dev-alice", "id": 54321},
            "html_url": "https://github.com/octocat/gitsentry-demo-repo/pull/42#issuecomment-778899",
        },
        "repository": {
            "id": 98765432,
            "name": "gitsentry-demo-repo",
            "full_name": "octocat/gitsentry-demo-repo",
            "private": False,
            "owner": {"login": "octocat", "id": 1},
        },
        "sender": {
            "login": "dev-alice",
            "id": 54321,
            "type": "User",
        },
        "installation": {
            "id": 999888,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Send synthetic GitHub webhooks with HMAC-SHA256 signature")
    parser.add_argument("--url", default="http://127.0.0.1:8000/webhook", help="Webhook receiver URL")
    parser.add_argument("--secret", default="test_webhook_secret_key_123", help="GitHub webhook secret")
    parser.add_argument("--event", choices=["ping", "pull_request", "issue_comment"], default="pull_request", help="GitHub Event Type")
    parser.add_argument("--action", default="opened", help="Event action (e.g. opened, synchronize, created)")
    parser.add_argument("--invalid-signature", action="store_true", help="Send deliberately invalid signature to test 401 rejection")

    args = parser.parse_args()

    delivery_id = str(uuid.uuid4())

    if args.event == "ping":
        payload_data = build_ping_payload()
    elif args.event == "pull_request":
        payload_data = build_pr_payload(action=args.action)
    elif args.event == "issue_comment":
        payload_data = build_comment_payload(action=args.action)
    else:
        payload_data = {}

    payload_bytes = json.dumps(payload_data).encode("utf-8")

    if args.invalid_signature:
        sig_header = "sha256=invalid00000000000000000000000000000000000000000000000000000000"
    else:
        sig_header = generate_github_signature(payload_bytes, args.secret)

    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": args.event,
        "X-GitHub-Delivery": delivery_id,
        "X-Hub-Signature-256": sig_header,
        "User-Agent": "GitHub-Hookshot/1.0",
    }

    print(f"--> Sending {args.event} (delivery {delivery_id}) to {args.url}")
    print(f"    Signature: {sig_header[:25]}...")

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(args.url, content=payload_bytes, headers=headers)
            print(f"<-- Response: HTTP {response.status_code}")
            try:
                print(f"    Body: {json.dumps(response.json(), indent=2)}")
            except Exception:
                print(f"    Body: {response.text}")
    except httpx.ConnectError:
        print(f"ERROR: Could not connect to {args.url}. Is the receiver service running?", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
