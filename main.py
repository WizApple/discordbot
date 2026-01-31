import discord
from discord.ext import commands, tasks
import json
import random
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()

# Bot Configuration
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Configuration - Edit these values or use commands
CONFIG = {
    "tracked_status": "discord.gg/robloxnepal",  # Status to track
    "status_role_name": "Supporter",  # Role to give when status is detected
    "check_interval": 1,  # How often to check statuses (in seconds)
}

# Data storage
giveaways = {}
status_tracker = {}

# Load data from file
def load_data():
    global giveaways, status_tracker
    try:
        with open('bot_data.json', 'r') as f:
            data = json.load(f)
            giveaways = data.get('giveaways', {})
            status_tracker = data.get('status_tracker', {})
            print(f"✅ Loaded {len(giveaways)} giveaways from storage")
    except FileNotFoundError:
        giveaways = {}
        status_tracker = {}
        print("📝 No existing data found, starting fresh")

# Save data to file
def save_data():
    with open('bot_data.json', 'w') as f:
        json.dump({
            'giveaways': giveaways,
            'status_tracker': status_tracker
        }, f, indent=4)

# Check if user has the required role
def has_status_role(member):
    role = discord.utils.get(member.guild.roles, name=CONFIG["status_role_name"])
    return role in member.roles if role else False

@bot.event
async def on_ready():
    print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print(f'✅ Bot logged in as {bot.user}')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'📊 Connected to {len(bot.guilds)} guild(s)')
    print(f'🎯 Tracking status: "{CONFIG["tracked_status"]}"')
    print(f'👥 Status role: "{CONFIG["status_role_name"]}"')
    print(f'⏱️  Check interval: {CONFIG["check_interval"]}s')
    print(f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    
    load_data()
    check_statuses.start()
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"for {CONFIG['tracked_status']} | !help"
        )
    )

@bot.event
async def on_raw_reaction_add(payload):
    """Remove reactions from users without the required role"""
    # Ignore bot reactions
    if payload.user_id == bot.user.id:
        return
    
    # Check if this is a giveaway message
    giveaway_id = str(payload.message_id)
    if giveaway_id not in giveaways:
        return
    
    # Check if the giveaway is still active
    if giveaways[giveaway_id]["ended"]:
        return
    
    # Only check for 🎉 emoji
    if str(payload.emoji) != "🎉":
        return
    
    # Get the member
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    
    member = guild.get_member(payload.user_id)
    if not member:
        return
    
    # Check if member has the required role
    if not has_status_role(member):
        # Remove the reaction
        try:
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)
            
            # Send a DM to the user explaining why
            try:
                embed = discord.Embed(
                    title="❌ Cannot Enter Giveaway",
                    description=(
                        f"You need the **{CONFIG['status_role_name']}** role to participate in this giveaway!\n\n"
                        f"Your reaction was removed automatically."
                    ),
                    color=discord.Color.from_str("#101b2c")
                )
                await member.send(embed=embed)
                print(f"🚫 Removed reaction from {member.name} (no {CONFIG['status_role_name']} role)")
            except discord.Forbidden:
                # User has DMs disabled, that's okay
                print(f"🚫 Removed reaction from {member.name} (couldn't DM)")
        except Exception as e:
            print(f"❌ Error removing reaction: {e}")

@tasks.loop(seconds=CONFIG["check_interval"])
async def check_statuses():
    """Periodically check user statuses and assign/remove roles"""
    for guild in bot.guilds:
        role = discord.utils.get(guild.roles, name=CONFIG["status_role_name"])
        
        if not role:
            continue
        
        for member in guild.members:
            if member.bot:
                continue
            
            has_correct_status = False
            
            # Check all activities
            if member.activities:
                for activity in member.activities:
                    # Check for game activity
                    if isinstance(activity, discord.Game):
                        if CONFIG["tracked_status"].lower() in activity.name.lower():
                            has_correct_status = True
                            break
                    # Check for streaming
                    elif isinstance(activity, discord.Streaming):
                        if "streaming" in CONFIG["tracked_status"].lower():
                            has_correct_status = True
                            break
                    # Check for custom status
                    elif isinstance(activity, discord.CustomActivity):
                        if activity.name and CONFIG["tracked_status"].lower() in activity.name.lower():
                            has_correct_status = True
                            break
                    # Check for listening/watching activities
                    elif isinstance(activity, discord.Spotify):
                        if "spotify" in CONFIG["tracked_status"].lower():
                            has_correct_status = True
                            break
                    # Check for other activities
                    elif hasattr(activity, 'name') and activity.name:
                        if CONFIG["tracked_status"].lower() in str(activity.name).lower():
                            has_correct_status = True
                            break
            
            # Assign or remove role based on status
            if has_correct_status and role not in member.roles:
                try:
                    await member.add_roles(role)
                    print(f"✅ Added {CONFIG['status_role_name']} to {member.name}")
                except discord.Forbidden:
                    print(f"❌ Missing permissions to add role to {member.name}")
                except Exception as e:
                    print(f"❌ Error adding role to {member.name}: {e}")
            elif not has_correct_status and role in member.roles:
                try:
                    await member.remove_roles(role)
                    print(f"🔻 Removed {CONFIG['status_role_name']} from {member.name}")
                except discord.Forbidden:
                    print(f"❌ Missing permissions to remove role from {member.name}")
                except Exception as e:
                    print(f"❌ Error removing role from {member.name}: {e}")

@check_statuses.before_loop
async def before_check_statuses():
    await bot.wait_until_ready()

@bot.command(name='setstatus')
@commands.has_permissions(administrator=True)
async def set_status(ctx, *, status_text: str):
    """Set the status to track (Admin only)
    Example: !setstatus Playing Minecraft
    """
    old_status = CONFIG["tracked_status"]
    CONFIG["tracked_status"] = status_text
    
    embed = discord.Embed(
        title="✅ Status Updated",
        description=f"**Old Status:** {old_status}\n**New Status:** {status_text}",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
    
    # Update bot presence
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"for {status_text} | !help"
        )
    )

@bot.command(name='setrolename')
@commands.has_permissions(administrator=True)
async def set_role_name(ctx, *, role_name: str):
    """Set the role name to assign (Admin only)
    Example: !setrolename Status VIP
    """
    old_role = CONFIG["status_role_name"]
    CONFIG["status_role_name"] = role_name
    
    embed = discord.Embed(
        title="✅ Role Name Updated",
        description=f"**Old Role:** {old_role}\n**New Role:** {role_name}",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='setinterval')
@commands.has_permissions(administrator=True)
async def set_interval(ctx, seconds: int):
    """Set the status check interval (Admin only)
    Example: !setinterval 120
    Minimum: 30 seconds
    """
    if seconds < 30:
        await ctx.send("❌ Interval must be at least 30 seconds!")
        return
    
    old_interval = CONFIG["check_interval"]
    CONFIG["check_interval"] = seconds
    
    # Restart the task with new interval
    check_statuses.cancel()
    check_statuses.change_interval(seconds=seconds)
    check_statuses.start()
    
    embed = discord.Embed(
        title="✅ Check Interval Updated",
        description=f"**Old Interval:** {old_interval}s\n**New Interval:** {seconds}s",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='createrole')
@commands.has_permissions(administrator=True)
async def create_role(ctx, color: Optional[str] = "blue"):
    """Create the status role if it doesn't exist (Admin only)
    Example: !createrole
    Example: !createrole red
    """
    role = discord.utils.get(ctx.guild.roles, name=CONFIG["status_role_name"])
    if role:
        await ctx.send(f"❌ Role **{CONFIG['status_role_name']}** already exists!")
        return
    
    # Color mapping
    color_map = {
        "red": discord.Color.red(),
        "blue": discord.Color.blue(),
        "green": discord.Color.green(),
        "gold": discord.Color.gold(),
        "purple": discord.Color.purple(),
        "orange": discord.Color.orange(),
    }
    
    role_color = color_map.get(color.lower(), discord.Color.blue())
    
    try:
        role = await ctx.guild.create_role(
            name=CONFIG["status_role_name"],
            color=role_color,
            reason="Status tracking role created by bot"
        )
        
        embed = discord.Embed(
            title="✅ Role Created",
            description=f"Successfully created role: **{CONFIG['status_role_name']}**",
            color=role_color
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to create roles!")

@bot.command(name='giveaway', aliases=['g', 'gstart'])
@commands.has_permissions(administrator=True)
async def start_giveaway(ctx, duration: str, winners: int, *, prize: str):
    """Start a giveaway (Admin only)
    Example: !giveaway 1h 1 Discord Nitro
    Duration format: 1m (minutes), 1h (hours), 1d (days)
    """
    # Parse duration
    time_units = {"m": 60, "h": 3600, "d": 86400}
    unit = duration[-1].lower()
    
    if unit not in time_units:
        await ctx.send("❌ Invalid duration! Use format like: 1m, 1h, or 1d")
        return
    
    try:
        amount = int(duration[:-1])
        seconds = amount * time_units[unit]
    except ValueError:
        await ctx.send("❌ Invalid duration format!")
        return
    
    if winners < 1:
        await ctx.send("❌ Must have at least 1 winner!")
        return
    
    # Create giveaway embed with accurate timestamp
    end_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    
    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉",
        description=(
            f"**Prize:** {prize}\n"
            f"**Winners:** {winners}\n"
            f"**Ends:** <t:{int(end_time.timestamp())}:R>\n\n"
            f"React with 🎉 to enter!\n\n"
            f"**🔒 Requirement:** Must have the **{CONFIG['status_role_name']}** role!"
        ),
        color=discord.Color.from_str("#101b2c")
    )
    embed.set_footer(text=f"Hosted by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    embed.timestamp = end_time
    
    giveaway_msg = await ctx.send(embed=embed)
    await giveaway_msg.add_reaction("🎉")
    
    # Store giveaway data
    giveaway_id = str(giveaway_msg.id)
    giveaways[giveaway_id] = {
        "channel_id": ctx.channel.id,
        "message_id": giveaway_msg.id,
        "prize": prize,
        "winners": winners,
        "end_time": end_time.isoformat(),
        "host_id": ctx.author.id,
        "ended": False
    }
    save_data()
    
    # Schedule end
    await asyncio.sleep(seconds)
    await end_giveaway(giveaway_id)

async def end_giveaway(giveaway_id: str):
    """End a giveaway and pick winners"""
    if giveaway_id not in giveaways or giveaways[giveaway_id]["ended"]:
        return
    
    giveaway = giveaways[giveaway_id]
    
    try:
        channel = bot.get_channel(giveaway["channel_id"])
        if not channel:
            print(f"❌ Channel not found for giveaway {giveaway_id}")
            return
            
        message = await channel.fetch_message(giveaway["message_id"])
        
        # Get reaction
        reaction = discord.utils.get(message.reactions, emoji="🎉")
        if not reaction:
            await channel.send(f"❌ Giveaway for **{giveaway['prize']}** ended but no one entered!")
            giveaway["ended"] = True
            save_data()
            return
        
        # Get users who reacted
        users = []
        async for user in reaction.users():
            if user.bot:
                continue
            
            member = channel.guild.get_member(user.id)
            if member and has_status_role(member):
                users.append(member)
        
        if not users:
            embed = discord.Embed(
                title="❌ Giveaway Ended - No Winners",
                description=f"**Prize:** {giveaway['prize']}\n\nNo eligible participants! Users must have the **{CONFIG['status_role_name']}** role to win.",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)
            giveaway["ended"] = True
            save_data()
            return
        
        # Pick winners
        winner_count = min(giveaway["winners"], len(users))
        winners = random.sample(users, winner_count)
        
        # Announce winners
        winner_mentions = ", ".join([w.mention for w in winners])
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY ENDED 🎉",
            description=(
                f"**Prize:** {giveaway['prize']}\n"
                f"**{'Winner' if len(winners) == 1 else 'Winners'}:** {winner_mentions}\n\n"
                f"Congratulations! 🎊"
            ),
            color=discord.Color.from_str("#101b2c")

        )
        embed.set_footer(text=f"{len(users)} eligible entries")
        
        await channel.send(content=winner_mentions, embed=embed)
        
        # Update original message
        original_embed = message.embeds[0]
        original_embed.color = discord.Color.red()
        original_embed.title = "🎉 GIVEAWAY ENDED 🎉"
        original_embed.description = (
            f"**Prize:** {giveaway['prize']}\n"
            f"**{'Winner' if len(winners) == 1 else 'Winners'}:** {winner_mentions}\n\n"
            f"**ENDED**"
        )
        await message.edit(embed=original_embed)
        
        giveaway["ended"] = True
        save_data()
        
        print(f"✅ Giveaway ended: {giveaway['prize']} - Winners: {[w.name for w in winners]}")
        
    except Exception as e:
        print(f"❌ Error ending giveaway {giveaway_id}: {e}")

@bot.command(name='reroll')
@commands.has_permissions(administrator=True)
async def reroll_giveaway(ctx, message_id: int):
    """Reroll a giveaway winner (Admin only)
    Example: !reroll 123456789
    """
    giveaway_id = str(message_id)
    
    if giveaway_id not in giveaways:
        await ctx.send("❌ Giveaway not found!")
        return
    
    if not giveaways[giveaway_id]["ended"]:
        await ctx.send("❌ This giveaway hasn't ended yet!")
        return
    
    giveaway = giveaways[giveaway_id]
    
    try:
        channel = bot.get_channel(giveaway["channel_id"])
        message = await channel.fetch_message(giveaway["message_id"])
        
        reaction = discord.utils.get(message.reactions, emoji="🎉")
        if not reaction:
            await ctx.send("❌ No entries found!")
            return
        
        users = []
        async for user in reaction.users():
            if user.bot:
                continue
            member = channel.guild.get_member(user.id)
            if member and has_status_role(member):
                users.append(member)
        
        if not users:
            await ctx.send("❌ No eligible participants!")
            return
        
        winner = random.choice(users)
        
        embed = discord.Embed(
            title="🔄 Giveaway Rerolled",
            description=f"**New Winner:** {winner.mention}\n**Prize:** {giveaway['prize']}\n\nCongratulations! 🎉",
            color=discord.Color.blue()
        )
        
        await ctx.send(content=winner.mention, embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error rerolling: {e}")

@bot.command(name='glist')
async def list_giveaways(ctx):
    """List all active giveaways"""
    active = [g for g in giveaways.values() if not g["ended"]]
    
    if not active:
        await ctx.send("📭 No active giveaways!")
        return
    
    embed = discord.Embed(
        title="📋 Active Giveaways",
        color=discord.Color.blue()
    )
    
    for g in active[:10]:  # Show max 10
        end_time = datetime.fromisoformat(g["end_time"])
        embed.add_field(
            name=f"🎁 {g['prize']}",
            value=f"Winners: {g['winners']}\nEnds: <t:{int(end_time.timestamp())}:R>",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='config')
async def show_config(ctx):
    """Show current bot configuration"""
    role = discord.utils.get(ctx.guild.roles, name=CONFIG["status_role_name"])
    role_exists = "✅ Exists" if role else "❌ Not found - use !createrole"
    
    members_with_role = len([m for m in ctx.guild.members if role and role in m.roles]) if role else 0
    
    embed = discord.Embed(
        title="⚙️ Bot Configuration",
        color=discord.Color.blue()
    )
    embed.add_field(name="🎯 Tracked Status", value=f"`{CONFIG['tracked_status']}`", inline=False)
    embed.add_field(name="👥 Role Name", value=CONFIG["status_role_name"], inline=True)
    embed.add_field(name="📊 Role Status", value=role_exists, inline=True)
    embed.add_field(name="👤 Members with Role", value=str(members_with_role), inline=True)
    embed.add_field(name="⏱️ Check Interval", value=f"{CONFIG['check_interval']} seconds", inline=True)
    embed.add_field(
        name="🎉 Active Giveaways",
        value=str(len([g for g in giveaways.values() if not g["ended"]])),
        inline=True
    )
    embed.add_field(
        name="📜 Total Giveaways",
        value=str(len(giveaways)),
        inline=True
    )
    
    embed.set_footer(text=f"Bot latency: {round(bot.latency * 1000)}ms")
    
    await ctx.send(embed=embed)

@bot.command(name='help', aliases=['h', 'commands'])
async def help_command(ctx):
    """Show all commands"""
    embed = discord.Embed(
        title="🤖 Discord Status Bot - Help",
        description="Track user statuses and run exclusive giveaways!",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="👤 Status Tracking (Admin)",
        value=(
            "`!setstatus <text>` - Set status to track\n"
            "`!setrolename <name>` - Set role name\n"
            "`!createrole [color]` - Create the status role\n"
            "`!setinterval <seconds>` - Set check interval"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎉 Giveaways (Admin)",
        value=(
            "`!giveaway <time> <winners> <prize>` - Start giveaway\n"
            "`!reroll <msg_id>` - Reroll winner\n"
            "**Example:** `!giveaway 1h 1 Discord Nitro`"
        ),
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Information",
        value=(
            "`!config` - View bot configuration\n"
            "`!glist` - List active giveaways\n"
            "`!help` - Show this message"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📌 How It Works",
        value=(
            "The bot checks user statuses automatically and assigns/removes roles.\n"
            "Only users with the status role can participate in giveaways!"
        ),
        inline=False
    )
    
    embed.set_footer(text="Use !config to see current settings")
    
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Missing Permissions",
            description="You need Administrator permissions to use this command!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument! Use `!help` for command usage.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        print(f"Error in command {ctx.command}: {error}")

# Run the bot
if __name__ == "__main__":
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 Starting Discord Status Bot...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Get token from environment variable or use placeholder
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ ERROR: No bot token found!")
        print("📝 Please set DISCORD_BOT_TOKEN in .env file")
        print("   Or edit this file and replace TOKEN")
        exit(1)
    
    # Start keep_alive web server
    keep_alive()
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ ERROR: Invalid bot token!")
        print("📝 Please check your token in .env file")
    except Exception as e:
        print(f"❌ ERROR: {e}")
