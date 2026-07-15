"""Services package — business logic and wrappers around external cloud APIs.

Every external service (storage, OCR, search, clinical trials, AI validation) is
isolated behind a wrapper here so controllers never talk to third-party APIs directly,
and so each integration can degrade to a documented fallback when unavailable.
"""
