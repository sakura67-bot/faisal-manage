import os
import json
import logging
import random
import asyncio
import aiohttp
import discord
from discord.ext import commands
from aiohttp import web

# =========================
# CONFIGURATION
# =========================

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))
PORT = int(os.getenv("PORT", 8080))

CONFIG_FILE = os.getenv("CONFIG_PATH", "config.json")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=">",
    intents=intents,
    help_command=None
)

# =========================
# RENDER KEEP-ALIVE HTTP SERVER
# =========================

async def handle_ping(request):
    return web.Response(text="Supreme is online and running on Render!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Render keep-alive server started on port {PORT}")


# =========================
# CUSTOM EMOJI CONFIGURATION
# =========================

EMOJIS = {
    "promo": "<a:giveaway:1559999666068791359>",
    "demo": "<:angry:1274605955035693057>",
    "shield": "<:z_mod_DiscordShield:1560000554909040694>",
    "gear": "<:Settings:1560007503239188594>",
    "ladder": "<:16400redswordrankicon:1560003340492865639>",
    "announcement": "<a:1369announce:1560000473623437376>",
    "audit": "<a:a7_book:1559999925822165105>",
    "success": "<a:MW_tick:1559999735329456220>",
    "warning": "<a:03_awarndns:1560000005492703303>",
    "error": "<a:error:1560000088732999810>",
    "user": "<:ntl_user:1556434847856328726>",
    "bullet": "<:MW_arrow_right:1560001178937598175>",
    "welcome": "<a:wel:1560947318277283893>",
    "ticket": "<:ticket:1560983848345665637>",
    "money": "<a:money:1567589905234661484>"
}

# Original emoji sources are kept so the bot can recreate app emojis after restarts.
EMOJI_SOURCES = dict(EMOJIS)

async def install_application_emojis():
    """Save source emoji images locally and create missing application emojis."""
    fetch_emojis = getattr(bot, "fetch_application_emojis", None)
    create_emoji = getattr(bot, "create_application_emoji", None)
    if not callable(fetch_emojis) or not callable(create_emoji):
        logging.warning("Automatic application emojis need discord.py 2.5 or newer.")
        return

    try:
        existing = {emoji.name: emoji for emoji in await fetch_emojis()}
    except Exception as exc:
        logging.warning("Could not fetch application emojis: %s", exc)
        return

    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "emojis")
    os.makedirs(folder, exist_ok=True)
    installed = 0

    async with aiohttp.ClientSession() as session:
        for name, source_markup in EMOJI_SOURCES.items():
            if name in existing:
                EMOJIS[name] = str(existing[name])
                continue

            source = discord.PartialEmoji.from_str(source_markup)
            if source.id is None:
                continue

            extension = "gif" if source.animated else "png"
            image_path = os.path.join(folder, f"{name}.{extension}")
            try:
                if os.path.isfile(image_path):
                    with open(image_path, "rb") as image_file:
                        image_data = image_file.read()
                else:
                    image_url = f"https://cdn.discordapp.com/emojis/{source.id}.{extension}?size=128&quality=lossless"
                    async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        response.raise_for_status()
                        image_data = await response.read()
                    if not image_data or len(image_data) > 256 * 1024:
                        raise ValueError("Emoji image must be non-empty and no larger than 256 KiB")
                    with open(image_path, "wb") as image_file:
                        image_file.write(image_data)

                created = await create_emoji(name=name, image=image_data)
                EMOJIS[name] = str(created)
                existing[name] = created
                installed += 1
            except Exception as exc:
                logging.warning("Could not install application emoji %s: %s", name, exc)

    logging.info("Application emoji setup finished; created %s new emojis.", installed)
config = {
    "supervisor_roles": {},
    "promodemo_channels": {},
    "audit_channels": {},
    "rank_ladders": {},
    "staff_limits": {},
    "economy": {},
    "extra_owners": {},
    "activity": {}
}


def load_config():
    global config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
        for key in config:
            if isinstance(saved.get(key), dict):
                config[key] = saved[key]
    except FileNotFoundError:
        save_config()
    except (json.JSONDecodeError, OSError):
        logging.exception("Could not load config file")


def save_config():
    temporary_file = CONFIG_FILE + ".tmp"
    try:
        with open(temporary_file, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
        os.replace(temporary_file, CONFIG_FILE)
    except OSError:
        logging.exception("Could not save configuration")


def economy_account(guild_id, user_id):
    guild_accounts = config.setdefault("economy", {}).setdefault(str(guild_id), {})
    account = guild_accounts.setdefault(str(user_id), {"balance": 0, "last_daily": 0, "last_work": 0})
    account["balance"] = max(0, int(account.get("balance", 0)))
    account.setdefault("last_daily", 0)
    account.setdefault("last_work", 0)
    return account


def economy_embed(message, color=discord.Color.blurple()):
    return discord.Embed(description=f"{EMOJIS['money']} {message}", color=color)

def guild_setting(setting, guild_id):
    return config[setting].get(str(guild_id))


# =========================
# PERMISSION & LIMIT HELPERS
# =========================

def user_is_owner(ctx):
    extra_ids = config.get("extra_owners", {}).get(str(ctx.guild.id), [])
    return ctx.author.id == OWNER_ID or ctx.author.id == ctx.guild.owner_id or str(ctx.author.id) in {str(uid) for uid in extra_ids}


def user_is_supervisor(ctx):
    if user_is_owner(ctx):
        return True
    role_id = guild_setting("supervisor_roles", ctx.guild.id)
    if not role_id:
        return False
    return any(role.id == int(role_id) for role in ctx.author.roles)


def user_is_staff(ctx):
    if user_is_supervisor(ctx) or ctx.author.guild_permissions.kick_members:
        return True
    return any("staff" in r.name.lower() or "trial" in r.name.lower() or "mod" in r.name.lower() for r in ctx.author.roles)


def check_and_increment_action_limit(ctx, action_type, limit=3):
    if user_is_supervisor(ctx):
        return True, 0

    import time
    now = time.time()
    user_id = str(ctx.author.id)

    if "staff_limits" not in config:
        config["staff_limits"] = {}

    if user_id not in config["staff_limits"]:
        config["staff_limits"][user_id] = {"kicks": [], "bans": []}

    timestamps = [t for t in config["staff_limits"][user_id].get(action_type, []) if now - t < 86400]

    if len(timestamps) >= limit:
        return False, len(timestamps)

    timestamps.append(now)
    config["staff_limits"][user_id][action_type] = timestamps
    save_config()
    return True, len(timestamps)


# =========================
# AUDIT LOGGING
# =========================

async def audit(guild, message):
    channel_id = guild_setting("audit_channels", guild.id)
    if not channel_id:
        return
    channel = guild.get_channel(int(channel_id))
    if channel is None:
        return
    try:
        await channel.send(message, allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        logging.exception("Failed to send audit log")


# =========================
# TICKET SYSTEM VIEWS
# =========================

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{EMOJIS['warning']} Closing ticket in 5 seconds...", ephemeral=False)
        await audit(interaction.guild, f"Ticket closed by {interaction.user} | Channel: {interaction.channel.name}")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Closed by {interaction.user}")
        except discord.HTTPException:
            pass


class TicketSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"{EMOJIS['error']} You already have an open ticket: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        supervisor_role_id = guild_setting("supervisor_roles", guild.id)
        if supervisor_role_id:
            sup_role = guild.get_role(int(supervisor_role_id))
            if sup_role:
                overwrites[sup_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        staff_team_role = discord.utils.find(lambda r: "staff team" in r.name.lower(), guild.roles)
        if staff_team_role:
            overwrites[staff_team_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        category = discord.utils.get(guild.categories, name="Support Tickets")
        if not category:
            category = await guild.create_category("Support Tickets")

        channel = await guild.create_text_channel(
            name=f"ticket-{member.name}",
            category=category,
            overwrites=overwrites,
            topic=f"Support ticket for {member} ({member.id})"
        )

        embed = discord.Embed(
            title=f"{EMOJIS['ticket']} Support Ticket",
            description=f"Hello {member.mention}! Support staff will be with you shortly.\nClick the button below when you are ready to close this ticket.",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Supreme • Ticket System")

        await channel.send(embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"{EMOJIS['success']} Your ticket has been created: {channel.mention}", ephemeral=True)
        await audit(guild, f"Ticket created by {member} ({member.id}) | Channel: {channel.name}")


# =========================
# EMBED HELPERS
# =========================

async def send_promodemo_embed(guild, member, role, action, moderator):
    channel_id = guild_setting("promodemo_channels", guild.id)
    if not channel_id:
        return
    channel = guild.get_channel(int(channel_id))
    if channel is None:
        return

    promoted = action == "promoted"
    embed = discord.Embed(
        title=f"{EMOJIS['promo']} Staff Promotion" if promoted else f"{EMOJIS['demo']} Staff Demotion",
        description=f"{member.mention} has been **promoted**!" if promoted else f"{member.mention} has been **demoted**.",
        color=discord.Color.green() if promoted else discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name=f"{EMOJIS['user']} Staff Member", value=f"{member.mention}\n`{member.id}`", inline=False)
    embed.add_field(name=f"{EMOJIS['ladder']} Role", value=role.mention, inline=True)
    embed.add_field(name=f"{EMOJIS['shield']} Action By", value=moderator.mention, inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"{guild.name} • Supreme System")

    try:
        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        pass


async def change_staff_role(ctx, member, target_role, action):
    if target_role is None:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} The specified or configured role could not be found in this server.", color=discord.Color.red()))
        return

    if member.id == ctx.author.id or member.id == ctx.guild.owner_id or target_role.is_default() or target_role.managed:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Action unauthorized or invalid role.", color=discord.Color.orange()))
        return

    try:
        if action == "promote":
            await member.add_roles(target_role, reason=f"Staff promotion by {ctx.author}")
            result = "promoted"
        else:
            await member.remove_roles(target_role, reason=f"Staff demotion by {ctx.author}")
            result = "demoted"

        await send_promodemo_embed(ctx.guild, member, target_role, result, ctx.author)
        await audit(ctx.guild, f"Staff {result}: {member} | Role: {target_role.name} | By: {ctx.author}")
        emoji = EMOJIS['promo'] if result == "promoted" else EMOJIS['demo']
        await ctx.reply(embed=discord.Embed(description=f"{emoji} {member.mention} was **{result}**: {target_role.mention}", color=discord.Color.green() if result == "promoted" else discord.Color.red()))
    except discord.Forbidden:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Missing permissions to modify roles.", color=discord.Color.red()))


# =========================
# MANAGEMENT & STAFF COMMANDS
# =========================

@bot.command(name="promo")
@commands.guild_only()
async def promo(ctx, staff: discord.Member, target_role: discord.Role = None):
    """Promotes a staff member."""
    if not user_is_supervisor(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    if target_role is None:
        ladder = config.get("rank_ladders", {}).get(str(ctx.guild.id))
        if not ladder:
            await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} No rank ladder configured. Add roles using `>ranks add @role`", color=discord.Color.orange()))
            return

        user_role_ids = [r.id for r in staff.roles]
        matched_index = -1
        
        for idx, r_id in enumerate(ladder):
            if r_id in user_role_ids:
                matched_index = idx

        next_index = matched_index + 1
        if next_index >= len(ladder):
            await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} {staff.mention} is already at the highest rank on the ladder!", color=discord.Color.orange()))
            return

        target_role = ctx.guild.get_role(ladder[next_index])

    await change_staff_role(ctx, staff, target_role, "promote")


@bot.command(name="demo")
@commands.guild_only()
async def demo(ctx, staff: discord.Member, target_role: discord.Role = None):
    """Demotes a staff member from their highest ladder rank."""
    if not user_is_supervisor(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    if target_role is None:
        ladder = config.get("rank_ladders", {}).get(str(ctx.guild.id))
        if not ladder:
            await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} No rank ladder configured. Add roles using `>ranks add @role`", color=discord.Color.orange()))
            return

        user_role_ids = [r.id for r in staff.roles]
        
        matched_index = -1
        for idx, r_id in enumerate(ladder):
            if r_id in user_role_ids:
                matched_index = idx

        if matched_index == -1:
            await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} {staff.mention} does not have any rank from the ladder!", color=discord.Color.orange()))
            return

        target_role = ctx.guild.get_role(ladder[matched_index])

    await change_staff_role(ctx, staff, target_role, "demote")


@bot.command(name="super")
@commands.guild_only()
async def super_cmd(ctx, member: discord.Member):
    """Assigns the supervisor role."""
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can use this command.", color=discord.Color.red()))
        return

    role_id = guild_setting("supervisor_roles", ctx.guild.id)
    if not role_id:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Supervisor role not set up.", color=discord.Color.orange()))
        return
    assigned_role = ctx.guild.get_role(int(role_id))
    if not assigned_role:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Configured supervisor role no longer exists.", color=discord.Color.red()))
        return
    await member.add_roles(assigned_role, reason=f"Supervisor assigned by {ctx.author}")
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Assigned supervisor role to {member.mention}.", color=discord.Color.green()))


@bot.command(name="superintro")
@commands.guild_only()
async def superintro(ctx):
    """Deletes the trigger message and introduces supervisor commands."""
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    if not user_is_supervisor(ctx):
        err_msg = await ctx.send(embed=discord.Embed(description=f"{EMOJIS['error']} Only staff supervisors can use this command.", color=discord.Color.red()))
        await err_msg.delete(delay=5)
        return

    embed = discord.Embed(
        title=f"{EMOJIS['welcome']} Welcome Staff Supervisor!",
        description=(
            f"Welcome to the **Supreme Supervisor System**! {EMOJIS['shield']}\n"
            "As a Supervisor, you have permission to manage the staff hierarchy using automated rank ladder commands."
        ),
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name=f"{EMOJIS['promo']} `>promo @member [@role]`",
        value=(
            f"{EMOJIS['bullet']} Promotes a staff member.\n"
            f"{EMOJIS['bullet']} **Auto Ladder:** If no role is given, advances them to the next step up."
        ),
        inline=False
    )

    embed.add_field(
        name=f"{EMOJIS['demo']} `>demo @member [@role]`",
        value=(
            f"{EMOJIS['bullet']} Demotes a staff member.\n"
            f"{EMOJIS['bullet']} **Auto Ladder:** If no role is given, strips their highest rank to drop them down."
        ),
        inline=False
    )

    embed.add_field(
        name=f"{EMOJIS['gear']} `>role @member @role`",
        value=f"{EMOJIS['bullet']} Quickly toggles an extra role on or off for a member.",
        inline=False
    )

    embed.set_footer(text=f"Requested by {ctx.author.display_name} • Supreme Guide", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name="staffintro")
@commands.guild_only()
async def staffintro(ctx):
    """Deletes the trigger message and introduces staff moderation commands."""
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    if not user_is_staff(ctx):
        err_msg = await ctx.send(embed=discord.Embed(description=f"{EMOJIS['error']} Only staff members can use this command.", color=discord.Color.red()))
        await err_msg.delete(delay=5)
        return

    embed = discord.Embed(
        title=f"{EMOJIS['welcome']} Welcome to the Supreme Staff Team!",
        description=(
            f"Hello {ctx.author.mention}! Thank you for keeping our community safe and active. {EMOJIS['shield']}\n"
            "Here is a quick introduction to your staff moderation tools and commands."
        ),
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name=f"{EMOJIS['warning']} Moderation Commands (Max 3 Kicks/Bans Per 24 Hours)",
        value=(
            f"{EMOJIS['bullet']} `>kick @member [reason]` — Kicks a disruptive user from the server.\n"
            f"{EMOJIS['bullet']} `>ban @member [reason]` — Permanently bans a rule-breaker.\n"
            f"{EMOJIS['bullet']} `>mute @member [reason]` — Times out a user for 10 minutes.\n"
            f"{EMOJIS['bullet']} `>clear [amount]` — Purges recent chat messages cleanly."
        ),
        inline=False
    )

    embed.add_field(
        name=f"{EMOJIS['user']} Utility & Information",
        value=(
            f"{EMOJIS['bullet']} `>userinfo [@member]` — Checks account creation, join dates, and roles.\n"
            f"{EMOJIS['bullet']} `>avatar [@member]` — Views high-resolution profile pictures."
        ),
        inline=False
    )

    embed.set_footer(text=f"Requested by {ctx.author.display_name} • Supreme Guide", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name="staff")
@commands.guild_only()
async def staff_cmd(ctx, member: discord.Member):
    """Assigns Staff Team and Trial Mod/Moderator roles automatically."""
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can use this command.", color=discord.Color.red()))
        return

    staff_team_role = discord.utils.find(lambda r: "staff team" in r.name.lower(), ctx.guild.roles)
    trial_mod_role = discord.utils.find(lambda r: "trial mod" in r.name.lower() or "trial moderator" in r.name.lower(), ctx.guild.roles)

    found_roles = [r for r in [staff_team_role, trial_mod_role] if r]
    if not found_roles:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Could not find 'Staff Team' or 'Trial Mod/Moderator' roles in this server.", color=discord.Color.red()))
        return

    await member.add_roles(*found_roles, reason=f"Staff roles assigned by {ctx.author}")
    assigned_mentions = ", ".join([r.mention for r in found_roles])
    
    embed = discord.Embed(
        title=f"{EMOJIS['success']} Staff Team Roles Assigned",
        description=f"Successfully assigned {assigned_mentions} to {member.mention}.",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Action by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.reply(embed=embed)
    await audit(ctx.guild, f"Staff roles ({assigned_mentions}) given to {member} ({member.id}) by {ctx.author}")


@bot.command(name="role")
@commands.guild_only()
async def role_cmd(ctx, member: discord.Member, target_role: discord.Role):
    """Toggles a role on a member."""
    if not user_is_supervisor(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    if target_role in member.roles:
        await member.remove_roles(target_role)
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['demo']} Removed {target_role.mention} from {member.mention}.", color=discord.Color.red()))
    else:
        await member.add_roles(target_role)
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['promo']} Added {target_role.mention} to {member.mention}.", color=discord.Color.green()))


@bot.command(name="steal")
@commands.guild_only()
async def steal(ctx, emoji: str, name: str = None):
    """Steals an emoji into the server."""
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can use this command.", color=discord.Color.red()))
        return

    import re
    match = re.match(r"<(a?):([a-zA-Z0-9_]+):([0-9]+)>", emoji)
    if not match:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Invalid custom emoji.", color=discord.Color.red()))
        return
    animated, e_name, e_id = match.groups()
    url = f"https://cdn.discordapp.com/emojis/{e_id}.{'gif' if animated=='a' else 'png'}?v=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            image_bytes = await resp.read()
    new_emoji = await ctx.guild.create_custom_emoji(name=name or e_name, image=image_bytes)
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Stole and added {new_emoji}!", color=discord.Color.green()))


# =========================
# TICKET SETUP COMMAND
# =========================

@bot.command(name="ticketsetup")
@commands.guild_only()
async def ticketsetup(ctx):
    """Deploys the persistent ticket creation panel."""
    if not user_is_supervisor(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the owners or supervisors can set up tickets.", color=discord.Color.red()))
        return

    embed = discord.Embed(
        title=f"{EMOJIS['ticket']} Support Ticket Center",
        description="Need assistance? Click the button below to open a private support ticket with our staff team.",
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="Supreme • Support System")

    await ctx.send(embed=embed, view=TicketSetupView())


# =========================
# MODERATION COMMANDS
# =========================

# =========================
# ECONOMY & ADMIN COMMANDS
# =========================

@bot.command(name="balance", aliases=["bal"])
@commands.guild_only()
async def balance(ctx, member: discord.Member = None):
    """Check your own or another member's wallet."""
    member = member or ctx.author
    account = economy_account(ctx.guild.id, member.id)
    await ctx.reply(embed=economy_embed(f"**{member.display_name}** has **{account['balance']:,}** coins."))


@bot.command(name="daily")
@commands.guild_only()
async def daily(ctx):
    """Claim a once-per-day coin reward."""
    import time
    account = economy_account(ctx.guild.id, ctx.author.id)
    remaining = 86400 - (int(time.time()) - int(account.get("last_daily", 0)))
    if remaining > 0:
        hours, minutes = divmod(remaining, 3600)
        await ctx.reply(embed=economy_embed(f"Your next daily reward is ready in **{hours}h {minutes // 60}m**."))
        return
    reward = random.randint(100, 250)
    account["balance"] += reward
    account["last_daily"] = int(time.time())
    save_config()
    await ctx.reply(embed=economy_embed(f"Daily reward claimed! You received **{reward}** coins. Balance: **{account['balance']:,}**."))


@bot.command(name="work", aliases=["job"])
@commands.guild_only()
async def work(ctx):
    """Work for a random coin reward; 60-second cooldown."""
    import time
    account = economy_account(ctx.guild.id, ctx.author.id)
    remaining = 60 - (int(time.time()) - int(account.get("last_work", 0)))
    if remaining > 0:
        await ctx.reply(embed=economy_embed(f"Catch your breath! You can work again in **{remaining}s**."))
        return
    reward = random.randint(20, 80)
    jobs = ["delivered a dragon's lunch", "organized a wizard's bookshelf", "DJ'd a tiny robot party", "found a pile of coins", "walked a very polite dinosaur"]
    account["balance"] += reward
    account["last_work"] = int(time.time())
    save_config()
    await ctx.reply(embed=economy_embed(f"You {random.choice(jobs)} and earned **{reward}** coins. Balance: **{account['balance']:,}**."))


@bot.command(name="pay", aliases=["transfer"])
@commands.guild_only()
async def pay(ctx, member: discord.Member, amount: int):
    """Send coins to another member."""
    if member.bot or member.id == ctx.author.id or not 1 <= amount <= 1000000:
        await ctx.reply(embed=economy_embed("Choose another member and an amount between 1 and 1,000,000."))
        return
    sender = economy_account(ctx.guild.id, ctx.author.id)
    if sender["balance"] < amount:
        await ctx.reply(embed=economy_embed("You don't have enough coins for that payment."))
        return
    recipient = economy_account(ctx.guild.id, member.id)
    sender["balance"] -= amount
    recipient["balance"] += amount
    save_config()
    await ctx.reply(embed=economy_embed(f"Sent **{amount:,}** coins to {member.mention}. Your balance is **{sender['balance']:,}**."))


@bot.command(name="leaderboard", aliases=["richlist", "topcoins"])
@commands.guild_only()
async def leaderboard(ctx):
    """Show the ten richest members in this server."""
    guild_accounts = config.setdefault("economy", {}).setdefault(str(ctx.guild.id), {})
    ranked = sorted(guild_accounts.items(), key=lambda item: int(item[1].get("balance", 0)), reverse=True)[:10]
    if not ranked:
        await ctx.reply(embed=economy_embed("No wallets yet. Start with `>daily`!"))
        return
    rows = [f"**{rank}.** <@{user_id}> — **{int(account.get('balance', 0)):,}** coins" for rank, (user_id, account) in enumerate(ranked, 1)]
    embed = economy_embed("🏆 **Coin Leaderboard**\n" + "\n".join(rows))
    await ctx.reply(embed=embed)


async def require_economy_admin(ctx):
    if user_is_supervisor(ctx):
        return True
    await ctx.reply(embed=economy_embed("Only the server owner or configured supervisor can manage member balances.", discord.Color.red()))
    return False


@bot.command(name="addmoney", aliases=["addcoins"])
@commands.guild_only()
async def addmoney(ctx, member: discord.Member, amount: int):
    """Admin: add coins to a member's wallet."""
    if not await require_economy_admin(ctx): return
    if not 1 <= amount <= 1000000000:
        await ctx.reply(embed=economy_embed("Amount must be from 1 to 1,000,000,000.")); return
    account = economy_account(ctx.guild.id, member.id)
    account["balance"] += amount
    save_config()
    await ctx.reply(embed=economy_embed(f"Added **{amount:,}** coins to {member.mention}. New balance: **{account['balance']:,}**."))


@bot.command(name="removemoney", aliases=["removecoins"])
@commands.guild_only()
async def removemoney(ctx, member: discord.Member, amount: int):
    """Admin: remove coins from a member's wallet."""
    if not await require_economy_admin(ctx): return
    if not 1 <= amount <= 1000000000:
        await ctx.reply(embed=economy_embed("Amount must be from 1 to 1,000,000,000.")); return
    account = economy_account(ctx.guild.id, member.id)
    removed = min(amount, account["balance"])
    account["balance"] -= removed
    save_config()
    await ctx.reply(embed=economy_embed(f"Removed **{removed:,}** coins from {member.mention}. New balance: **{account['balance']:,}**."))


@bot.command(name="setmoney", aliases=["setcoins"])
@commands.guild_only()
async def setmoney(ctx, member: discord.Member, amount: int):
    """Admin: set a member's wallet balance."""
    if not await require_economy_admin(ctx): return
    if not 0 <= amount <= 1000000000:
        await ctx.reply(embed=economy_embed("Balance must be from 0 to 1,000,000,000.")); return
    account = economy_account(ctx.guild.id, member.id)
    previous = account["balance"]
    account["balance"] = amount
    save_config()
    await ctx.reply(embed=economy_embed(f"Set {member.mention}'s balance from **{previous:,}** to **{amount:,}** coins."))


@bot.command(name="resetmoney", aliases=["resetcoins"])
@commands.guild_only()
async def resetmoney(ctx, member: discord.Member = None):
    """Admin: reset one member's wallet, or the whole server economy."""
    if not await require_economy_admin(ctx): return
    accounts = config.setdefault("economy", {}).setdefault(str(ctx.guild.id), {})
    if member:
        account = economy_account(ctx.guild.id, member.id)
        account.update({"balance": 0, "last_daily": 0, "last_work": 0})
        message = f"Reset {member.mention}'s wallet."
    else:
        accounts.clear()
        message = "Reset every wallet in this server."
    save_config()
    await ctx.reply(embed=economy_embed(message, discord.Color.orange()))

@bot.command(name="kick")
@commands.guild_only()
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kicks a member (Staff capped at 3 per 24 hours)."""
    if not user_is_staff(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    allowed, count = check_and_increment_action_limit(ctx, "kicks", limit=3)
    if not allowed:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} You have reached your limit of **3 kicks per 24 hours**.", color=discord.Color.orange()))
        return

    try:
        await member.kick(reason=f"{reason} (Kicked by {ctx.author})")
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Kicked {member.mention} | Reason: {reason}", color=discord.Color.orange()))
        await audit(ctx.guild, f"Member kicked: {member} ({member.id}) | Reason: {reason} | By: {ctx.author}")
    except discord.Forbidden:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} I lack permissions to kick that member.", color=discord.Color.red()))


@bot.command(name="ban")
@commands.guild_only()
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    """Bans a member (Staff capped at 3 per 24 hours)."""
    if not user_is_staff(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    allowed, count = check_and_increment_action_limit(ctx, "bans", limit=3)
    if not allowed:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} You have reached your limit of **3 bans per 24 hours**.", color=discord.Color.orange()))
        return

    try:
        await member.ban(reason=f"{reason} (Banned by {ctx.author})")
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Banned {member.mention} | Reason: {reason}", color=discord.Color.red()))
        await audit(ctx.guild, f"Member banned: {member} ({member.id}) | Reason: {reason} | By: {ctx.author}")
    except discord.Forbidden:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} I lack permissions to ban that member.", color=discord.Color.red()))


@bot.command(name="clear")
@commands.guild_only()
async def clear(ctx, amount: int = 5):
    """Purges messages."""
    if not user_is_staff(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=discord.Embed(description=f"{EMOJIS['success']} Cleared {amount} messages.", color=discord.Color.green()))
    await msg.delete(delay=3)


@bot.command(name="mute")
@commands.guild_only()
async def mute(ctx, member: discord.Member, *, reason="No reason provided"):
    """Timeouts a member."""
    if not user_is_staff(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    from datetime import timedelta
    try:
        await member.timeout(timedelta(minutes=10), reason=f"{reason} (Muted by {ctx.author})")
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Timed out {member.mention} for 10 minutes.", color=discord.Color.orange()))
        await audit(ctx.guild, f"Member timed out: {member} ({member.id}) | Reason: {reason} | By: {ctx.author}")
    except discord.Forbidden:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} I lack permissions to timeout that member.", color=discord.Color.red()))


# =========================
# UTILITY & INFO COMMANDS
# =========================

@bot.command(name="ping")
@commands.guild_only()
async def ping(ctx):
    """Shows bot latency."""
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Pong! Latency: `{round(bot.latency * 1000)}ms`", color=discord.Color.blue()))


@bot.command(name="serverinfo")
@commands.guild_only()
async def serverinfo(ctx):
    """Shows server info."""
    g = ctx.guild
    embed = discord.Embed(title=f"{EMOJIS['gear']} {g.name} Information", color=discord.Color.blurple())
    embed.add_field(name=f"{EMOJIS['user']} Owner", value=g.owner, inline=True)
    embed.add_field(name=f"{EMOJIS['ladder']} Members", value=g.member_count, inline=True)
    embed.add_field(name=f"{EMOJIS['success']} Created On", value=g.created_at.strftime("%Y-%m-%d"), inline=True)
    await ctx.reply(embed=embed)


@bot.command(name="userinfo")
@commands.guild_only()
async def userinfo(ctx, member: discord.Member = None):
    """Shows user info."""
    m = member or ctx.author
    embed = discord.Embed(title=f"{EMOJIS['user']} {m} Info", color=m.color)
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="ID", value=m.id, inline=True)
    embed.add_field(name="Joined", value=m.joined_at.strftime("%Y-%m-%d") if m.joined_at else "N/A", inline=True)
    await ctx.reply(embed=embed)


@bot.command(name="avatar")
@commands.guild_only()
async def avatar(ctx, member: discord.Member = None):
    """Shows user avatar."""
    m = member or ctx.author
    embed = discord.Embed(title=f"{EMOJIS['user']} Avatar for {m}", color=discord.Color.blurple())
    embed.set_image(url=m.display_avatar.url)
    await ctx.reply(embed=embed)


# =========================
# FUN & MISC COMMANDS
# =========================

@bot.command(name="coinflip")
async def coinflip(ctx):
    """Flips a coin."""
    result = random.choice(["Heads", "Tails"])
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} The coin landed on: **{result}**", color=discord.Color.gold()))


@bot.command(name="roll")
async def roll(ctx):
    """Rolls a dice (1-6)."""
    result = random.randint(1, 6)
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} You rolled a **{result}**!", color=discord.Color.gold()))


# =========================
# SETUP COMMANDS (RANKS ADD / CLEAR)
# =========================

@bot.group(invoke_without_command=True)
@commands.guild_only()
async def ranks(ctx):
    """Shows current rank ladder configuration."""
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can use this command.", color=discord.Color.red()))
        return

    ladder = config.get("rank_ladders", {}).get(str(ctx.guild.id), [])
    ladder_str = " -> ".join([f"<@&{r_id}>" for r_id in ladder]) if ladder else "Not configured. Use `>ranks add @role`"
    
    embed = discord.Embed(
        title=f"{EMOJIS['ladder']} Staff Rank Ladder",
        description=f"**Current Order (Lowest to Highest):**\n{ladder_str}",
        color=discord.Color.blurple()
    )
    await ctx.reply(embed=embed)


@ranks.command(name="add")
@commands.guild_only()
async def ranks_add(ctx, role: discord.Role):
    """Adds a role to the rank ladder sequence (lowest to highest)."""
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can use this command.", color=discord.Color.red()))
        return

    if role.is_default() or role.managed:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} You cannot add that role to the ladder.", color=discord.Color.orange()))
        return

    guild_id = str(ctx.guild.id)
    if "rank_ladders" not in config:
        config["rank_ladders"] = {}
    if guild_id not in config["rank_ladders"]:
        config["rank_ladders"][guild_id] = []

    if role.id in config["rank_ladders"][guild_id]:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} That role is already in the rank ladder.", color=discord.Color.orange()))
        return

    config["rank_ladders"][guild_id].append(role.id)
    save_config()

    ladder = config["rank_ladders"][guild_id]
    ladder_str = " -> ".join([f"<@&{r_id}>" for r_id in ladder])

    embed = discord.Embed(
        title=f"{EMOJIS['success']} Rank Added to Ladder",
        description=f"Added {role.mention} successfully!\n\n**Current Ladder:**\n{ladder_str}",
        color=discord.Color.green()
    )
    await ctx.reply(embed=embed)


@ranks.command(name="clear")
@commands.guild_only()
async def ranks_clear(ctx):
    """Clears the entire rank ladder configuration."""
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can use this command.", color=discord.Color.red()))
        return

    guild_id = str(ctx.guild.id)
    if "rank_ladders" in config and guild_id in config["rank_ladders"]:
        config["rank_ladders"][guild_id] = []
        save_config()

    embed = discord.Embed(
        title=f"{EMOJIS['success']} Rank Ladder Cleared",
        description="The rank ladder sequence has been reset.",
        color=discord.Color.red()
    )
    await ctx.reply(embed=embed)


@bot.command(name="setstaffsupervisor")
@commands.guild_only()
async def setstaffsupervisor(ctx, assigned_role: discord.Role):
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can use this command.", color=discord.Color.red()))
        return

    config["supervisor_roles"][str(ctx.guild.id)] = assigned_role.id
    save_config()
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Supervisor role set to {assigned_role.mention}.", color=discord.Color.green()))


@bot.command(name="setpromodemo")
@commands.guild_only()
async def setpromodemo(ctx, channel: discord.TextChannel):
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can use this command.", color=discord.Color.red()))
        return

    config["promodemo_channels"][str(ctx.guild.id)] = channel.id
    save_config()
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Promo channel set to {channel.mention}.", color=discord.Color.green()))


@bot.command(name="setaudit")
@commands.guild_only()
async def setaudit(ctx, channel: discord.TextChannel):
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can use this command.", color=discord.Color.red()))
        return

    config["audit_channels"][str(ctx.guild.id)] = channel.id
    save_config()
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Audit channel set to {channel.mention}.", color=discord.Color.green()))


@bot.command(name="staffsettings")
@commands.guild_only()
async def staffsettings(ctx):
    """Displays current server staff configurations and rank ladder."""
    if not user_is_supervisor(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to view staff settings.", color=discord.Color.red()))
        return

    supervisor_id = guild_setting("supervisor_roles", ctx.guild.id)
    promo_id = guild_setting("promodemo_channels", ctx.guild.id)
    audit_id = guild_setting("audit_channels", ctx.guild.id)
    ladder = config.get("rank_ladders", {}).get(str(ctx.guild.id), [])

    supervisor = ctx.guild.get_role(int(supervisor_id)) if supervisor_id else None
    promo_channel = ctx.guild.get_channel(int(promo_id)) if promo_id else None
    audit_channel = ctx.guild.get_channel(int(audit_id)) if audit_id else None
    
    ladder_str = " -> ".join([f"<@&{r_id}>" for r_id in ladder]) if ladder else "Not configured (`>ranks add @role`)"

    embed = discord.Embed(
        title=f"{EMOJIS['gear']} Supreme • Server Settings",
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name=f"{EMOJIS['shield']} Supervisor Role",
        value=supervisor.mention if supervisor else "Not configured (`>setstaffsupervisor @role`)",
        inline=False
    )
    embed.add_field(
        name=f"{EMOJIS['announcement']} Announcement Channel",
        value=promo_channel.mention if promo_channel else "Not configured (`>setpromodemo #channel`)",
        inline=False
    )
    embed.add_field(
        name=f"{EMOJIS['audit']} Audit Log Channel",
        value=audit_channel.mention if audit_channel else "Not configured (`>setaudit #channel`)",
        inline=False
    )
    embed.add_field(
        name=f"{EMOJIS['ladder']} Rank Ladder Sequence",
        value=ladder_str,
        inline=False
    )
    embed.add_field(
        name=f"{EMOJIS['warning']} Staff Daily Quota",
        value="Max **3 Kicks / 3 Bans per 24 hours** for Staff Members",
        inline=False
    )

    embed.set_footer(text=f"{ctx.guild.name} • Configuration Dashboard", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    await ctx.reply(embed=embed)


# =========================
# HELP COMMAND
# =========================

# =========================
# EXTRA OWNER & BOT ACTIVITY COMMANDS
# =========================

@bot.command(name="addextraowner")
@commands.guild_only()
async def addextraowner(ctx, member: discord.Member):
    """Give a member owner-level bot permissions in this server."""
    if not (ctx.author.id == OWNER_ID or ctx.author.id == ctx.guild.owner_id):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can add extra owners.", color=discord.Color.red()))
        return
    if member.bot:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Bots cannot be added as extra owners.", color=discord.Color.orange()))
        return
    owners = config.setdefault("extra_owners", {}).setdefault(str(ctx.guild.id), [])
    if str(member.id) in {str(uid) for uid in owners}:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} {member.mention} is already an extra owner.", color=discord.Color.orange()))
        return
    owners.append(str(member.id))
    save_config()
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Added {member.mention} as an extra owner for this server.", color=discord.Color.green()))


@bot.command(name="removextraowner", aliases=["removeextraowner"])
@commands.guild_only()
async def removextraowner(ctx, member: discord.Member):
    """Remove a member's owner-level bot permissions in this server."""
    if not (ctx.author.id == OWNER_ID or ctx.author.id == ctx.guild.owner_id):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner or server owner can remove extra owners.", color=discord.Color.red()))
        return
    owners = config.setdefault("extra_owners", {}).setdefault(str(ctx.guild.id), [])
    if str(member.id) not in {str(uid) for uid in owners}:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} {member.mention} is not an extra owner.", color=discord.Color.orange()))
        return
    config["extra_owners"][str(ctx.guild.id)] = [str(uid) for uid in owners if str(uid) != str(member.id)]
    save_config()
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Removed {member.mention} from the extra owners.", color=discord.Color.green()))


ACTIVITY_TYPES = {
    "playing": discord.ActivityType.playing,
    "listening": discord.ActivityType.listening,
    "watching": discord.ActivityType.watching,
    "competing": discord.ActivityType.competing,
    "streaming": discord.ActivityType.streaming,
}


async def apply_bot_activity(activity_type, text):
    if activity_type == "playing":
        activity = discord.Game(name=text)
    elif activity_type == "streaming":
        activity = discord.Streaming(name=text, url="https://www.twitch.tv/")
    else:
        activity = discord.Activity(type=ACTIVITY_TYPES[activity_type], name=text)
    await bot.change_presence(activity=activity, status=discord.Status.online)


@bot.command(name="setactivity")
@commands.guild_only()
async def setactivity(ctx, activity: str, *, text: str):
    """Set the bot's global status, for example >setactivity playing Supreme Bot."""
    if not user_is_owner(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to change the bot activity.", color=discord.Color.red()))
        return
    activity = activity.lower()
    if activity not in ACTIVITY_TYPES:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Activity must be playing, streaming, listening, watching, or competing.", color=discord.Color.orange()))
        return
    text = text.strip()
    if not text or len(text) > 128:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Activity text must be between 1 and 128 characters.", color=discord.Color.orange()))
        return
    try:
        await apply_bot_activity(activity, text)
        config["activity"] = {"type": activity, "text": text}
        save_config()
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Bot activity set to **{activity.title()} {text}**.", color=discord.Color.green()))
    except discord.HTTPException as exc:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Discord couldn't update that activity: `{exc}`", color=discord.Color.red()))

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title=f"{EMOJIS['gear']} Supreme • Command Center", description="Here are all available command modules:", color=discord.Color.blurple())
    embed.add_field(name=f"{EMOJIS['shield']} Staff & Management", value="`>promo`, `>demo`, `>super`, `>superintro`, `>staffintro`, `>staff`, `>role`, `>steal`", inline=False)
    embed.add_field(name=f"{EMOJIS['warning']} Moderation", value="`>kick`, `>ban`, `>clear`, `>mute`", inline=False)
    embed.add_field(name=f"{EMOJIS['money']} Economy", value="`>balance [@member]`, `>daily`, `>work`, `>pay @member amount`, `>leaderboard`", inline=False)
    embed.add_field(name=f"{EMOJIS['money']} Economy Admin (Owner/Supervisor)", value="`>addmoney @member amount`, `>removemoney @member amount`, `>setmoney @member amount`, `>resetmoney [@member]`", inline=False)
    embed.add_field(name=f"{EMOJIS['ticket']} Support & Tickets", value="`>ticketsetup`", inline=False)
    embed.add_field(name=f"{EMOJIS['user']} Utility & Info", value="`>ping`, `>serverinfo`, `>userinfo`, `>avatar`", inline=False)
    embed.add_field(name=f"{EMOJIS['success']} Fun & Games", value="`>coinflip`, `>roll`", inline=False)
    embed.add_field(name=f"{EMOJIS['gear']} Setup", value="`>ranks add @role`, `>ranks clear`, `>setstaffsupervisor`, `>setpromodemo`, `>setaudit`, `>staffsettings`, `>addextraowner @member`, `>removextraowner @member`, `>setactivity <playing|streaming|listening|watching|competing> <text>`", inline=False)
    await ctx.reply(embed=embed, mention_author=False)


# =========================
# EVENTS & STARTUP
# =========================

@bot.event
async def on_ready():
    bot.add_view(TicketSetupView())
    bot.add_view(TicketCloseView())
    await install_application_emojis()
    activity_settings = config.get("activity", {})
    if activity_settings.get("type") in ACTIVITY_TYPES and activity_settings.get("text"):
        await apply_bot_activity(activity_settings["type"], activity_settings["text"])
    logging.info("Supreme logged in as %s", bot.user)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return
    
    logging.exception("Command error:", exc_info=error)
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Error: `{str(error)}`", color=discord.Color.red()))


async def main():
    load_config()
    asyncio.create_task(start_web_server())
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())














