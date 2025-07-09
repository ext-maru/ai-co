
# Mock BeautifulSoup for testing
class BeautifulSoup:
    def __init__(self, html, parser=None):
        self.html = html
        self.parser = parser
    
    def find(self, *args, **kwargs):
        return None
    
    def find_all(self, *args, **kwargs):
        return []
    
    def get_text(self):
        return ""
