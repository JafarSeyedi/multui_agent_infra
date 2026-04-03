class HallucinationGuard:

    def __init__(self):

        self.strict_mode = False

    def enable_strict_mode(self):

        self.strict_mode = True

    def disable(self):

        self.strict_mode = False
