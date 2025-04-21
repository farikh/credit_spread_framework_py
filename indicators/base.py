class BaseIndicator:
    def calculate(self, bars):
        raise NotImplementedError("Must implement in subclass")
