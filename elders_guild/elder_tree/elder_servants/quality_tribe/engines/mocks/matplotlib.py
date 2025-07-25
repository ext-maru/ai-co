# Mock matplotlib for testing
class pyplot:
    """pyplotクラス"""
    @staticmethod
    def plot(*args, **kwargs):
        pass

    @staticmethod
    def show(*args, **kwargs):
        pass

    @staticmethod
    def savefig(*args, **kwargs):
        pass

    @staticmethod
    def figure(*args, **kwargs):
        pass

    @staticmethod
    def xlabel(*args, **kwargs):
        pass

    @staticmethod
    def ylabel(*args, **kwargs):
        pass

    @staticmethod
    def title(*args, **kwargs):
        pass


plt = pyplot
