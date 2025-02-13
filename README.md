# Pickleball Discord Bot

A Discord bot that lets users play a strategic pickleball game by choosing different shots to outmaneuver their opponents.

## Features

- Challenge other players to matches
- Five different shot types with rock-paper-scissors style interactions
- Score tracking and game status monitoring
- Private shot selection through DMs
- Automatic round resolution and scoring
- Match status tracking and forfeit options

## Shot System

Each shot type has specific advantages over others:

- **Drive**
  - Beats: Dink, Drop
  - Countered by: Lob, Smash

- **Lob**
  - Beats: Drive, Drop
  - Countered by: Dink, Smash

- **Dink**
  - Beats: Drop, Lob
  - Countered by: Drive, Smash

- **Drop**
  - Beats: Drive, Smash
  - Countered by: Dink, Lob

- **Smash**
  - Beats: Dink, Lob
  - Countered by: Drop

## Setup

1. Clone this repository
2. Install required dependencies:
```bash
pip install discord.py python-dotenv
```
3. Create a `.env` file in the project root with your Discord bot token:
```
DISCORD_TOKEN=your_token_here
```
4. Run the bot:
```bash
python bot.py
```

## Commands

- `!pb-challenge @player` - Challenge another player to a match
- `!pb-accept` - Accept a pending challenge
- `!pb-shot <shot>` - Make your shot (use in DMs with the bot)
- `!pb-status` - Check the current match status
- `!pb-forfeit` - Forfeit the current match
- `!pb-rules` - Display game rules and valid commands

## Game Rules

1. First player to 11 points wins
2. Must win by 2 points
3. Points are awarded by winning rounds
4. Rounds are won by choosing a shot that beats your opponent's shot
5. Tied rounds result in no points awarded
6. Shots must be made privately through DMs with the bot

## Technical Details

The bot uses:
- `discord.py` for Discord integration
- Environment variables for secure token storage
- Dictionary-based shot relationship system
- Match state tracking through memory storage

## Match Structure

Matches are stored in a dictionary with the following structure:
```python
{
    "players": [player1_id, player2_id],
    "shots": {player1_id: shot, player2_id: shot},
    "score": {player1_id: score, player2_id: score},
    "current_player": player_id,
    "winner": winner_id,
    "started_at": timestamp,
    "round": round_number,
    "status": "pending|active|completed"
}
```
