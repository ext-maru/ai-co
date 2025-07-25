"""
selenium module
"""

try:
    from selenium import webdriver
except ImportError:
    selenium = None
