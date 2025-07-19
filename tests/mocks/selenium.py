# Mock selenium for testing
class webdriver:
    class Chrome:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, url):
            pass

        def quit(self):
            pass

        def find_element(self, by, value):
            return None

        def find_elements(self, by, value):
            return []

    class Firefox:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, url):
            pass

        def quit(self):
            pass


class By:
    ID = "id"
    NAME = "name"
    CLASS_NAME = "class name"
    CSS_SELECTOR = "css selector"
    XPATH = "xpath"
