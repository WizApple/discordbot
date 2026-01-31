# Discord Status Bot 🤖

A Discord bot that tracks user statuses and runs exclusive giveaways for users with specific statuses.

## Features

✅ **Status Tracking** - Automatically assign roles to users with specific statuses  
🎉 **Exclusive Giveaways** - Run giveaways only for users with the status role  
⚙️ **Configurable** - Customize status text, role names, and check intervals  
💾 **Persistent Data** - Saves giveaway data across restarts  

## Commands

### Admin Commands

- `!setstatus <text>` - Set the status to track
- `!setrolename <name>` - Set the role name to assign
- `!createrole [color]` - Create the status role
- `!setinterval <seconds>` - Set status check interval (min: 30s)
- `!giveaway <time> <winners> <prize>` - Start a giveaway
- `!reroll <message_id>` - Reroll a giveaway winner

### Public Commands

- `!config` - View current bot configuration
- `!glist` - List active giveaways
- `!help` - Show all commands

## Deployment on Render.com

### 1. Prerequisites

- A Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- A GitHub account
- A Render.com account (free tier works!)

### 2. Setup Steps

#### Step 1: Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Go to "Bot" section and click "Add Bot"
4. Under "Privileged Gateway Intents", enable:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent
5. Copy your bot token (you'll need this later!)

#### Step 2: Push to GitHub

1. Create a new repository on GitHub
2. Upload these files:
   - `main.py`
   - `keep_alive.py`
   - `requirements.txt`
   - `.gitignore`
   - `README.md`
3. **DO NOT** upload `.env` file!

#### Step 3: Deploy on Render.com

1. Go to [Render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `discord-status-bot` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: `Free`
5. Add Environment Variable:
   - **Key**: `DISCORD_BOT_TOKEN`
   - **Value**: Your Discord bot token
6. Click "Create Web Service"

### 4. Invite Bot to Server

Use this URL (replace `YOUR_CLIENT_ID` with your bot's client ID from Discord Developer Portal):

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=268446720&scope=bot
```

**Required Permissions:**
- Manage Roles
- Send Messages
- Embed Links
- Add Reactions
- Read Message History
- Use External Emojis

## Local Development

### Setup

1. Clone the repository
2. Create `.env` file:
   ```
   DISCORD_BOT_TOKEN=your_bot_token_here
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the bot:
   ```bash
   python main.py
   ```

## Configuration

Edit `CONFIG` in `main.py`:

```python
CONFIG = {
    "tracked_status": "discord.gg/yourserver",  # Status to track
    "status_role_name": "Supporter",            # Role name
    "check_interval": 1,                        # Check every N seconds
}
```

Or use commands:
- `!setstatus discord.gg/yourserver`
- `!setrolename Supporter`
- `!setinterval 60`

## How It Works

1. **Status Monitoring**: Bot checks all members' statuses every N seconds
2. **Role Assignment**: If status matches, user gets the role automatically
3. **Role Removal**: If status doesn't match, role is removed
4. **Giveaways**: Only users with the status role can enter giveaways
5. **Auto-moderation**: Non-eligible reactions are automatically removed

## Example Usage

```bash
# Set the status to track
!setstatus discord.gg/robloxnepal

# Create the role
!createrole blue

# Start a 1-hour giveaway with 1 winner
!giveaway 1h 1 Discord Nitro

# Check configuration
!config
```

## Troubleshooting

### Bot not responding?
- Check if bot is online in Discord
- Verify bot has proper permissions
- Check Render.com logs for errors

### Roles not being assigned?
- Ensure bot role is higher than the status role
- Check bot has "Manage Roles" permission
- Verify status text matches exactly (case-insensitive)

### Giveaways not working?
- Users must have the status role first
- Check if bot has "Add Reactions" permission
- Ensure message hasn't been deleted

## Support

For issues or questions:
1. Check the logs on Render.com
2. Use `!config` to verify settings
3. Make sure all bot permissions are correct

## License

MIT License - Feel free to modify and use!

---
s
