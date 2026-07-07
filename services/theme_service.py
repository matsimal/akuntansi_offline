class ThemeService:

    def __init__(self, db):
        self.db = db

    def load(self):
        return self.db.get_theme()

    def save(self, data):
        self.db.save_theme(data)