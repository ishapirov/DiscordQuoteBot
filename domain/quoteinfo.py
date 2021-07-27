class QuoteInfo:
    def __init__(self,row: tuple):
        self.quote_id = row[0]
        self.author = row[1].capitalize()
        self.quote = row[2]
        self.like = row[3]
        self.interesting = row[4]

    def like_leaderboard_format(self) -> str:
        return f"Likes: {self.like} \"{self.quote}\" - {self.author} (ID: {self.quote_id})"

    def interesting_leaderboard_format(self) -> str:
        return f"Interesting Score: {self.interesting} \"{self.quote}\" - {self.author} (ID:{self.quote_id})"

    def __repr__(self) -> str:
        return f"\"{self.quote}\" - {self.author}\nLikes: {self.like}, Interesting Score: {self.interesting} (ID: {self.quote_id})"