class Session:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.username = None

    def set_auth(self, token: str, user_id: int, username: str):
        self.token = token
        self.user_id = user_id
        self.username = username

SESSION = Session()
