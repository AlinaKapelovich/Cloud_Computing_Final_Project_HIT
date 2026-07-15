"""Controllers package — Flask blueprints that receive HTTP requests.

Controllers stay thin: they validate input, call services/models, and return a
rendered template (View) or a redirect. They never call external cloud APIs directly.
"""
