from datetime import date

class Message:

    def __init__(self, question):
        # get today's date
        today = date.today()

        # convert to string (YYYY-MM-DD format)
        self.date_posted = today.strftime("%Y-%m-%d")
        self.question = question
        self.likes = 0
        self.replies = {}

        