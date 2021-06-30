# Discord Quote Bot

Developed for a Discord server to allow for people to save and read quotes said by each other.  
The server has 2 channels. One called *#quotes* where people post quotes in the format:  
**"Quote goes here" - Author_Name**  

The other channel #quotes-pull is where people pull quotes from the bot through different commands.  
Each pulled quote can be reacted to with emotes, and there is a leaderboard for the top emoted quotes.  
A pulled quote has the format:  
**"Quote goes here" - Author_Name  
Likes: \*number_of_likes\*, Interesting Score: \*number_of_interesting_reactions\* (ID: \*quote_id\*)**  

List of commands:

- **!quote**: Returns a random quote made by any author
- **!quotefrom author_name**: Returns a random quote made by a specific author
- **!delete quote_id**: Deletes a quote with the provided id
- **!leaderboard**: Generates a leaderboard of the top 10 quotes with the highest like score (Most thumbs-up reactions)  
- **!interesting**: Generates a leaderboard of the top 10 quotes with the highest interesting score (Most eyes reactions)  