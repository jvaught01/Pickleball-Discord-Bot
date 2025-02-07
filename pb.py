import discord
from discord.ext import commands
from datetime import datetime, timedelta


intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(command_prefix="!", intents=intents)


current_matches = {}


SHOTS = {
    "drive": {"beats": ["dink", "drop"]},
    "lob": {"beats": ["drive", "drop"]},
    "dink": {"beats": ["drop", "lob"]},
    "drop": {"beats": ["drive", "smash"]},
    "smash": {"beats": ["dink", "lob"]},
}

WINNING_SCORE = 11
POINT_DIFFERENCE = 2

def get_match_by_player(player_id):
    for match_id, match in current_matches.items():
        if player_id in match["players"]:
            return match_id
    return None

def determine_round_winner(shot1, shot2):
    if shot1 == shot2:
        return None
    if shot2 in SHOTS[shot1]["beats"]:
        return 0  # First player wins
    if shot1 in SHOTS[shot2]["beats"]:
        return 1  # Second player wins
    return None

@bot.command(name="pb-challenge")
async def pb_challenge(ctx, opponent: discord.Member):
    if opponent == ctx.author:
        await ctx.send("You can't challenge yourself!")
        return
    
    if get_match_by_player(opponent.id):
        await ctx.send("This player is already in a match!")
        return
    
    if get_match_by_player(ctx.author.id):
        await ctx.send("You are already in a match!")
        return
    
    match_id = f"{ctx.author.id}-{opponent.id}"
    current_matches[match_id] = {
        "players": [ctx.author.id, opponent.id],
        "shots": {ctx.author.id: None, opponent.id: None},
        "score": {ctx.author.id: 0, opponent.id: 0},
        "current_player": ctx.author.id,
        "winner": None,
        "started_at": ctx.message.created_at,
        "round": 1,
        "status": "pending"  # pending, active, completed
    }
    
    await ctx.send(f"{ctx.author.mention} has challenged {opponent.mention} to a game of pickleball! Use !pb-accept to accept.")

@bot.command(name="pb-accept")
async def pb_accept(ctx):
    # Find any match where this player was challenged
    match_id = None
    for mid, match in current_matches.items():
        if match["players"][1] == ctx.author.id and match["status"] == "pending":
            match_id = mid
            break
    
    if not match_id:
        await ctx.send("You don't have any pending challenges!")
        return
    
    match = current_matches[match_id]
    challenger = await bot.fetch_user(match["players"][0])
    
    match["status"] = "active"
    await ctx.send(f"{ctx.author.mention} has accepted the challenge! Game starting with {challenger.mention}. Use !pb-shot to play!")

@bot.command(name="pb-shot")
async def pb_shot(ctx, shot: str):
    # Delete the command message immediately to hide the shot
    await ctx.message.delete()
    
    match_id = get_match_by_player(ctx.author.id)
    if not match_id:
        await ctx.send("You are not in a match!", delete_after=5)
        return
    
    match = current_matches[match_id]
    
    if match["status"] != "active":
        await ctx.send("This match hasn't started or is already finished!", delete_after=5)
        return
    
    if match["current_player"] != ctx.author.id:
        await ctx.send("It's not your turn!", delete_after=5)
        return
    
    if shot.lower() not in SHOTS:
        valid_shots = ", ".join(SHOTS.keys())
        await ctx.send(f"Invalid shot! Valid shots are: {valid_shots}", delete_after=5)
        return
    
    # Record the shot
    match["shots"][ctx.author.id] = shot.lower()
    
    # Find opponent
    opponent_id = match["players"][0] if match["players"][1] == ctx.author.id else match["players"][1]
    opponent = await bot.fetch_user(opponent_id)
    
    # Send private confirmation that auto-deletes after 2 seconds
    await ctx.send(f"Your shot has been recorded!", delete_after=2)
    
    # Send public message about the turn
    await ctx.send(f"{ctx.author.mention} has made their shot! Waiting for {opponent.mention}...")
    
    # Switch current player
    match["current_player"] = opponent_id
    
    # If both players have shot, resolve the round
    if match["shots"][match["players"][0]] and match["shots"][match["players"][1]]:
        shot1 = match["shots"][match["players"][0]]
        shot2 = match["shots"][match["players"][1]]
        
        winner_idx = determine_round_winner(shot1, shot2)
        
        if winner_idx is not None:
            winner_id = match["players"][winner_idx]
            match["score"][winner_id] += 1
            winner = await bot.fetch_user(winner_id)
            await ctx.send(f"{winner.mention} wins the round! ({shot1} beats {shot2})")
        else:
            await ctx.send("It's a tie! No points awarded.")
        
        # Reset for next round
        match["round"] += 1
        match["shots"] = {player_id: None for player_id in match["players"]}
        
        # Check for game winner
        for player_id, score in match["score"].items():
            if score >= WINNING_SCORE and score - match["score"][opponent_id] >= POINT_DIFFERENCE:
                match["winner"] = player_id
                match["status"] = "completed"
                winner = await bot.fetch_user(player_id)
                await ctx.send(f"🏆 {winner.mention} wins the game! Final score: {match['score']}")
                return
        
        # Show current score
        player1 = await bot.fetch_user(match["players"][0])
        player2 = await bot.fetch_user(match["players"][1])
        await ctx.send(f"Score: {player1.name}: {match['score'][player1.id]} - {player2.name}: {match['score'][player2.id]}")

@bot.command(name="pb-forfeit")
async def pb_forfeit(ctx):
    match_id = get_match_by_player(ctx.author.id)
    if not match_id:
        await ctx.send("You are not in a match!")
        return
    
    match = current_matches[match_id]
    opponent_id = match["players"][0] if match["players"][1] == ctx.author.id else match["players"][1]
    opponent = await bot.fetch_user(opponent_id)
    
    match["winner"] = opponent_id
    match["status"] = "completed"
    
    await ctx.send(f"{ctx.author.mention} has forfeited the match. {opponent.mention} wins!")

@bot.command(name="pb-status")
async def pb_status(ctx):
    match_id = get_match_by_player(ctx.author.id)
    if not match_id:
        await ctx.send("You are not in a match!")
        return
    
    match = current_matches[match_id]
    player1 = await bot.fetch_user(match["players"][0])
    player2 = await bot.fetch_user(match["players"][1])
    
    status_msg = (
        f"Match Status:\n"
        f"Players: {player1.name} vs {player2.name}\n"
        f"Score: {match['score'][player1.id]} - {match['score'][player2.id]}\n"
        f"Round: {match['round']}\n"
        f"Status: {match['status']}\n"
    )
    
    if match["status"] == "active":
        current_player = await bot.fetch_user(match["current_player"])
        status_msg += f"Current turn: {current_player.name}"
    
    await ctx.send(status_msg)

@bot.command(name="pb-rules")
async def pb_rules(ctx):
    valid_shots = ", ".join(SHOTS.keys())
    
    rules = f"""
🏓 **Pickleball Discord Game Rules** 🏓

**Game Setup:**
• Challenge someone with `!pb-challenge @player`
• Accept a challenge with `!pb-accept`

**Making Shots:**
• Use `!pb-shot <shot>` in DMs with the bot
• Valid shots: `{valid_shots}`

**Shot Relationships:**
• Drive beats: Dink, Drop
• Lob beats: Drive, Drop
• Dink beats: Drop, Lob
• Drop beats: Drive, Smash
• Smash beats: Dink, Lob

**Scoring:**
• First to {WINNING_SCORE} points wins
• Must win by {POINT_DIFFERENCE} points
• Win a round to score a point
• Ties result in no points

**Other Commands:**
• Check game status: `!pb-status`
• Forfeit a game: `!pb-forfeit`
• View these rules: `!pb-rules`

**Remember:** Make your shots in DMs to keep them private from your opponent!
"""
    await ctx.send(rules)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

# Add your bot token here
bot.run('MTMzNzI5NjkxNzczODAzMzE4Mw.GX08db.qt7KH_1eMU-9drgPvEeQvyHKlGnA0G-zLzUaZ4')


