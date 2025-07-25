"""
flask module
"""

try:
    from flask import Flask
except ImportError:
    flask = None
