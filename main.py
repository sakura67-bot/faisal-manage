import os
import json
import logging
import random
import asyncio
import secrets
import time
import urllib.parse
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
PORT = int(os.getenv("SERVER_PORT", os.getenv("PORT", 8080)))
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "")
WEB_SESSIONS = {}

CONFIG_FILE = os.getenv("CONFIG_PATH", "config.json")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


def dynamic_prefix(bot_instance, message):
    guild_id = str(message.guild.id) if message.guild else ""
    configured = config.get("prefixes", {}).get(guild_id, ">") if "config" in globals() else ">"
    return commands.when_mentioned_or(configured)(bot_instance, message)


bot = commands.Bot(
    command_prefix=dynamic_prefix,
    intents=intents,
    help_command=None
)

# =========================
# BOT-HOSTING.NET WEB DASHBOARD
# =========================

DASHBOARD_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Supreme Bot Dashboard</title>
<style>
:root{color-scheme:dark;--bg:#0c1020;--card:#171d32;--line:#2a3453;--accent:#9b7bff;--text:#f4f2ff;--muted:#aab2cc}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 0,#25204b,var(--bg) 45%);font:16px system-ui,sans-serif;color:var(--text);min-height:100vh}.wrap{max-width:1050px;margin:0 auto;padding:34px 20px}.tag{color:#c3b5ff;font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:12px}.hero{margin:22px 0}.card{background:linear-gradient(145deg,#1b223b,#151a2c);border:1px solid var(--line);border-radius:18px;padding:22px;margin:17px 0;box-shadow:0 20px 55px #05071266}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.field{display:flex;flex-direction:column;gap:8px;margin:10px 0}label{font-weight:650;color:#dedaff}input,select,textarea{background:#10162a;color:var(--text);border:1px solid #394365;border-radius:10px;padding:12px;font:inherit;width:100%}textarea{min-height:115px;resize:vertical}button,.button{display:inline-flex;align-items:center;justify-content:center;background:var(--accent);color:#111225;border:0;border-radius:10px;padding:12px 18px;font-weight:750;text-decoration:none;cursor:pointer;margin:6px 8px 0 0}button.secondary{background:#2b3554;color:var(--text)}.bar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.status{min-height:26px;color:#b8f3d1;margin-top:12px}.small{font-size:13px;color:var(--muted)}.hidden{display:none}.row{display:flex;gap:10px;align-items:center}h1{font-size:clamp(30px,5vw,46px);margin:8px 0}h2{margin:0 0 7px}p{color:var(--muted);line-height:1.55}.preview{white-space:pre-wrap;background:#10162a;border-left:4px solid var(--accent);padding:14px;border-radius:8px;min-height:70px;color:#ddd}@media(max-width:700px){.grid{grid-template-columns:1fr}.wrap{padding:20px 14px}.card{padding:16px}}
</style></head><body><main class="wrap"><div class="bar"><div><div class="tag">Supreme Bot • Bot-Hosting.net</div><div class="small">Server dashboard</div></div><button class="secondary" onclick="logout()">Log out</button></div>
<section class="hero"><h1>Bot control panel</h1><p>Manage the server settings and publish panels or embeds. Choose a server where you have management access and Supreme Bot is installed.</p></section>
<section class="card"><div class="field"><label for="guild">Discord server</label><select id="guild"></select></div><div id="settings" class="hidden"><h2>Server settings</h2><p class="small">Prefix, staff destinations, embed appearance, and ticket panel content are saved per server.</p><div class="grid">
<div class="field"><label for="prefix">Command prefix</label><input id="prefix" maxlength="5" value=">"><span class="small">Example: `>` or `!`</span></div>
<div class="field"><label for="supervisor">Supervisor role</label><select id="supervisor"></select></div>
<div class="field"><label for="promodemo">Promotion / demotion channel</label><select id="promodemo"></select></div><div class="field"><label for="audit">Audit log channel</label><select id="audit"></select></div>
<div class="field"><label for="embedColor">Default embed color</label><input id="embedColor" type="color" value="#5865f2"></div><div class="field"><label for="footer">Default embed footer</label><input id="footer" maxlength="200" placeholder="Supreme Bot"></div>
<div class="field"><label for="ticketTitle">Ticket panel title</label><input id="ticketTitle" maxlength="100"></div><div class="field"><label for="ticketChannel">Ticket panel channel</label><select id="ticketChannel"></select></div>
<div class="field"><label for="ticketDescription">Ticket panel description</label><textarea id="ticketDescription" maxlength="2000"></textarea></div>
<div class="field"><label for="dailyMin">Daily reward minimum</label><input id="dailyMin" type="number" min="0" max="1000000"></div><div class="field"><label for="dailyMax">Daily reward maximum</label><input id="dailyMax" type="number" min="0" max="1000000"></div><div class="field"><label for="workMin">Work reward minimum</label><input id="workMin" type="number" min="0" max="1000000"></div><div class="field"><label for="workMax">Work reward maximum</label><input id="workMax" type="number" min="0" max="1000000"></div><div class="field"><label for="workCooldown">Work cooldown (seconds)</label><input id="workCooldown" type="number" min="10" max="86400"></div>
</div><button onclick="saveSettings()">Save server settings</button><button class="secondary" onclick="postPanel()">Post ticket dropdown</button><div id="settingsStatus" class="status"></div></div><div id="empty" class="small hidden">No servers found where you manage settings and Supreme Bot is installed.</div></section>
<section id="moneyCard" class="card hidden"><h2>Economy manager</h2><p class="small">Change a member’s coins. Your Discord account needs server management access.</p><div class="grid"><div class="field"><label for="moneyUser">Member ID</label><input id="moneyUser" inputmode="numeric" placeholder="Discord user ID"></div><div class="field"><label for="moneyAction">Action</label><select id="moneyAction"><option value="add">Add coins</option><option value="remove">Remove coins</option><option value="set">Set balance</option><option value="reset">Reset wallet</option></select></div><div class="field"><label for="moneyAmount">Amount</label><input id="moneyAmount" type="number" min="0" max="1000000000" value="100"></div></div><button onclick="manageMoney()">Apply economy change</button><div id="moneyStatus" class="status"></div></section><section id="embedCard" class="card hidden"><h2>Embed builder</h2><p class="small">Create and send a custom embed to a channel. Field rows use `name | value | inline`; use `true` or `false` for inline.</p><div class="grid"><div class="field"><label for="embedChannel">Post in</label><select id="embedChannel"></select></div><div class="field"><label for="customColor">Embed color</label><input id="customColor" type="color" value="#5865f2"></div><div class="field"><label for="customTitle">Title</label><input id="customTitle" maxlength="256" placeholder="Announcement"></div><div class="field"><label for="customFooter">Footer</label><input id="customFooter" maxlength="200" placeholder="Optional footer"></div>
<div class="field"><label for="customAuthor">Author label</label><input id="customAuthor" maxlength="256" placeholder="Optional author"></div><div class="field"><label for="customUrl">Title link (HTTPS URL)</label><input id="customUrl" maxlength="2048" placeholder="https://example.com"></div><div class="field"><label for="customImage">Image URL (HTTPS)</label><input id="customImage" maxlength="2048" placeholder="https://example.com/image.png"></div><div class="field"><label for="customThumb">Thumbnail URL (HTTPS)</label><input id="customThumb" maxlength="2048" placeholder="https://example.com/thumb.png"></div><div class="field"><label for="customDescription">Description</label><textarea id="customDescription" maxlength="4000" placeholder="Write your embed message"></textarea></div><div class="field"><label for="customFields">Fields (one per line)</label><textarea id="customFields" placeholder="Rules | Be kind to everyone | false&#10;Need help? | Open a ticket below | true"></textarea></div></div><div class="preview" id="preview">Embed preview will appear here.</div><button onclick="sendEmbed()">Send embed</button><div id="embedStatus" class="status"></div></section>
<section id="activityCard" class="card hidden"><h2>Bot activity</h2><p class="small">This changes the bot-wide Discord presence. Only the bot owner can save it.</p><div class="grid"><div class="field"><label for="activityType">Activity</label><select id="activityType"><option>playing</option><option>streaming</option><option>listening</option><option>watching</option><option>competing</option></select></div><div class="field"><label for="activityText">Activity text</label><input id="activityText" maxlength="128" placeholder="Supreme Bot"></div></div><button class="secondary" onclick="saveActivity()">Save activity</button><div id="activityStatus" class="status"></div></section>
<p class="small">The website runs inside this bot deployment. Activate a Bot-Hosting.net HTTPS subdomain and set the Discord OAuth redirect URL to `/oauth/callback`.</p></main>
<script>
const guildSelect=document.getElementById('guild'),settings=document.getElementById('settings'),statusBox=document.getElementById('settingsStatus');
async function api(path,options={}){const response=await fetch(path,{credentials:'same-origin',headers:{'Content-Type':'application/json',...(options.headers||{})},...options});if(response.status===401){location.href='/login';throw new Error('Please sign in again.')}const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');return data}
function fill(id,items,selected,label){const el=document.getElementById(id);el.replaceChildren(new Option(label,''));for(const item of items)el.add(new Option(item.name,item.id));if(selected)el.value=String(selected)}
async function loadGuilds(){try{const data=await api('/api/guilds');if(!data.guilds.length){document.getElementById('empty').classList.remove('hidden');return}for(const g of data.guilds)guildSelect.add(new Option(g.name,g.id));await loadConfig()}catch(e){statusBox.textContent=e.message}}
async function loadConfig(){try{const d=await api('/api/guild/'+guildSelect.value);fill('supervisor',d.roles,d.supervisor_role,'No supervisor role');fill('promodemo',d.channels,d.promodemo_channel,'Not set');fill('audit',d.channels,d.audit_channel,'Not set');fill('ticketChannel',d.channels,null,'Choose a channel');fill('embedChannel',d.channels,null,'Choose a channel');document.getElementById('prefix').value=d.prefix;document.getElementById('embedColor').value=d.embed_color;document.getElementById('footer').value=d.embed_footer;document.getElementById('ticketTitle').value=d.ticket_title;document.getElementById('ticketDescription').value=d.ticket_description;document.getElementById('dailyMin').value=d.economy.daily_min;document.getElementById('dailyMax').value=d.economy.daily_max;document.getElementById('workMin').value=d.economy.work_min;document.getElementById('workMax').value=d.economy.work_max;document.getElementById('workCooldown').value=d.economy.work_cooldown;document.getElementById('activityType').value=d.activity_type||'playing';document.getElementById('activityText').value=d.activity_text||'';document.getElementById('activityCard').classList.toggle('hidden',!d.can_set_activity);settings.classList.remove('hidden');document.getElementById('moneyCard').classList.remove('hidden');document.getElementById('embedCard').classList.remove('hidden');document.getElementById('empty').classList.add('hidden')}catch(e){statusBox.textContent=e.message}}
guildSelect.addEventListener('change',loadConfig);
async function saveSettings(){statusBox.textContent='Saving…';try{await api('/api/guild/'+guildSelect.value+'/settings',{method:'POST',body:JSON.stringify({prefix:document.getElementById('prefix').value,supervisor_role:document.getElementById('supervisor').value,promodemo_channel:document.getElementById('promodemo').value,audit_channel:document.getElementById('audit').value,embed_color:document.getElementById('embedColor').value,embed_footer:document.getElementById('footer').value,ticket_title:document.getElementById('ticketTitle').value,ticket_description:document.getElementById('ticketDescription').value,daily_min:Number(document.getElementById('dailyMin').value),daily_max:Number(document.getElementById('dailyMax').value),work_min:Number(document.getElementById('workMin').value),work_max:Number(document.getElementById('workMax').value),work_cooldown:Number(document.getElementById('workCooldown').value)})});statusBox.textContent='Settings saved.'}catch(e){statusBox.textContent=e.message}}
async function postPanel(){const channel=document.getElementById('ticketChannel').value;if(!channel){statusBox.textContent='Choose a ticket panel channel first.';return}statusBox.textContent='Posting…';try{await api('/api/guild/'+guildSelect.value+'/ticket-panel',{method:'POST',body:JSON.stringify({channel_id:channel})});statusBox.textContent='Ticket dropdown posted.'}catch(e){statusBox.textContent=e.message}}
function updatePreview(){const title=document.getElementById('customTitle').value,description=document.getElementById('customDescription').value;document.getElementById('preview').textContent=(title?'◆ '+title+'\n':'')+(description||'Embed preview will appear here.');document.getElementById('preview').style.borderColor=document.getElementById('customColor').value}
['customTitle','customDescription','customColor'].forEach(id=>document.getElementById(id).addEventListener('input',updatePreview));
async function sendEmbed(){const channel=document.getElementById('embedChannel').value;if(!channel){document.getElementById('embedStatus').textContent='Choose a channel first.';return}const fields=document.getElementById('customFields').value.split('\n').map(x=>x.trim()).filter(Boolean).map(line=>{const p=line.split('|');return{name:(p[0]||'').trim(),value:(p[1]||'').trim(),inline:(p[2]||'').trim().toLowerCase()==='true'}});const box=document.getElementById('embedStatus');box.textContent='Sending…';try{await api('/api/guild/'+guildSelect.value+'/embed',{method:'POST',body:JSON.stringify({channel_id:channel,title:document.getElementById('customTitle').value,description:document.getElementById('customDescription').value,color:document.getElementById('customColor').value,footer:document.getElementById('customFooter').value,author:document.getElementById('customAuthor').value,title_url:document.getElementById('customUrl').value,image_url:document.getElementById('customImage').value,thumbnail_url:document.getElementById('customThumb').value,fields})});box.textContent='Embed sent.'}catch(e){box.textContent=e.message}}
async function manageMoney(){const box=document.getElementById('moneyStatus');box.textContent='Saving…';try{await api('/api/guild/'+guildSelect.value+'/money',{method:'POST',body:JSON.stringify({user_id:document.getElementById('moneyUser').value,action:document.getElementById('moneyAction').value,amount:Number(document.getElementById('moneyAmount').value)})});box.textContent='Wallet updated.'}catch(e){box.textContent=e.message}}
async function saveActivity(){const box=document.getElementById('activityStatus');box.textContent='Saving…';try{await api('/api/activity',{method:'POST',body:JSON.stringify({type:document.getElementById('activityType').value,text:document.getElementById('activityText').value})});box.textContent='Activity updated.'}catch(e){box.textContent=e.message}}
async function logout(){await fetch('/logout',{method:'POST',credentials:'same-origin'});location.href='/'}loadGuilds();
</script></body></html>"""
LANDING_HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Supreme Bot</title><style>body{margin:0;background:#101326;color:#f4f2ff;font:17px system-ui;min-height:100vh;display:grid;place-items:center}.card{max-width:620px;margin:20px;padding:38px;background:#1b2037;border:1px solid #343c5e;border-radius:20px}h1{font-size:42px;margin:10px 0}p{color:#b6bfd8;line-height:1.6}.button{display:inline-block;background:#9b7bff;color:#101020;padding:13px 18px;border-radius:10px;font-weight:bold;text-decoration:none}.note{font-size:14px}</style></head><body><main class="card"><div>SUPREME BOT • DASHBOARD</div><h1>Configure your server</h1><p>Sign in with Discord to manage your server prefix, staff settings, ticket panels, embeds, economy, and more.</p><a class="button" href="/login">Continue with Discord</a><p class="note">The bot must already be invited to your server. Set DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, and DISCORD_REDIRECT_URI in the hosting environment to enable sign-in.</p></main></body></html>"""


def get_web_session(request):
    session_id = request.cookies.get("supreme_session")
    session = WEB_SESSIONS.get(session_id)
    if session and session["expires"] > time.time():
        return session
    if session_id:
        WEB_SESSIONS.pop(session_id, None)
    return None


def web_user_can_manage(session, guild_id):
    guild_info = next((g for g in session.get("guilds", []) if str(g.get("id")) == str(guild_id)), None)
    if not guild_info:
        return False
    try:
        permissions = int(guild_info.get("permissions", "0"))
    except (TypeError, ValueError):
        permissions = 0
    owner = bool(guild_info.get("owner"))
    extra_owner = str(session["user"]["id"]) in {str(uid) for uid in config.get("extra_owners", {}).get(str(guild_id), [])}
    bot_owner = int(OWNER_ID) > 0 and str(session["user"]["id"]) == str(OWNER_ID)
    return bot_owner or owner or extra_owner or bool(permissions & 0x8) or bool(permissions & 0x20)


def response_json_error(message, status=400):
    return web.json_response({"error": message}, status=status)


async def handle_ping(request):
    if get_web_session(request):
        raise web.HTTPFound("/dashboard")
    return web.Response(text=LANDING_HTML, content_type="text/html")


async def handle_dashboard(request):
    if not get_web_session(request):
        raise web.HTTPFound("/")
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")


async def handle_login(request):
    if not (DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET and DISCORD_REDIRECT_URI):
        return web.Response(text="Set DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, and DISCORD_REDIRECT_URI in the hosting environment first.", status=503)
    state = secrets.token_urlsafe(24)
    params = urllib.parse.urlencode({"client_id": DISCORD_CLIENT_ID, "redirect_uri": DISCORD_REDIRECT_URI, "response_type": "code", "scope": "identify guilds", "state": state, "prompt": "consent"})
    response = web.HTTPFound("https://discord.com/oauth2/authorize?" + params)
    response.set_cookie("supreme_oauth_state", state, max_age=600, httponly=True, secure=True, samesite="Lax")
    raise response


async def handle_oauth_callback(request):
    state = request.query.get("state", "")
    if not state or state != request.cookies.get("supreme_oauth_state"):
        return web.Response(text="Login state expired. Please try again.", status=400)
    code = request.query.get("code")
    if not code:
        return web.Response(text="Discord login was cancelled.", status=400)
    token_data = {"client_id": DISCORD_CLIENT_ID, "client_secret": DISCORD_CLIENT_SECRET, "grant_type": "authorization_code", "code": code, "redirect_uri": DISCORD_REDIRECT_URI}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://discord.com/api/v10/oauth2/token", data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"}) as response:
                tokens = await response.json(content_type=None)
                if response.status != 200:
                    return web.Response(text="Discord token exchange failed. Check the dashboard OAuth settings.", status=502)
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            async with session.get("https://discord.com/api/v10/users/@me", headers=headers) as response:
                user = await response.json(content_type=None)
                if response.status != 200:
                    return web.Response(text="Could not verify your Discord account.", status=502)
            async with session.get("https://discord.com/api/v10/users/@me/guilds", headers=headers) as response:
                guilds = await response.json(content_type=None)
                if response.status != 200:
                    return web.Response(text="Could not read your Discord server list.", status=502)
    except (aiohttp.ClientError, asyncio.TimeoutError, KeyError):
        logging.exception("Discord OAuth request failed")
        return web.Response(text="Discord login could not be completed. Please try again.", status=502)

    session_id = secrets.token_urlsafe(32)
    WEB_SESSIONS[session_id] = {"user": {"id": str(user["id"]), "username": user.get("username", "Discord user")}, "guilds": guilds, "expires": time.time() + 12 * 60 * 60}
    result = web.HTTPFound("/dashboard")
    result.set_cookie("supreme_session", session_id, max_age=12 * 60 * 60, httponly=True, secure=True, samesite="Lax")
    result.del_cookie("supreme_oauth_state")
    raise result


async def handle_logout(request):
    session_id = request.cookies.get("supreme_session")
    if session_id:
        WEB_SESSIONS.pop(session_id, None)
    response = web.json_response({"ok": True})
    response.del_cookie("supreme_session")
    return response


async def web_authorized_guild(request):
    session = get_web_session(request)
    if not session:
        return None, None, response_json_error("Sign in with Discord first.", 401)
    guild_id = request.match_info["guild_id"]
    if not web_user_can_manage(session, guild_id):
        return None, None, response_json_error("You do not have permission to configure this server.", 403)
    guild = bot.get_guild(int(guild_id))
    if guild is None:
        return None, None, response_json_error("Supreme Bot is not in that server.", 404)
    return session, guild, None


async def handle_api_guilds(request):
    session = get_web_session(request)
    if not session:
        return response_json_error("Sign in with Discord first.", 401)
    result = []
    for info in session.get("guilds", []):
        guild = bot.get_guild(int(info["id"]))
        if guild and web_user_can_manage(session, guild.id):
            result.append({"id": str(guild.id), "name": guild.name})
    return web.json_response({"guilds": sorted(result, key=lambda item: item["name"].lower())})


async def handle_api_guild(request):
    _, guild, error = await web_authorized_guild(request)
    if error:
        return error
    gid = str(guild.id)
    roles = [{"id": str(role.id), "name": role.name} for role in guild.roles if not role.is_default() and not role.managed]
    channels = [{"id": str(channel.id), "name": "#" + channel.name} for channel in guild.text_channels]
    embed_settings = get_embed_settings(gid)
    ticket_settings = get_ticket_settings(gid)
    activity_settings = config.get("activity", {})
    session = get_web_session(request)
    return web.json_response({
        "roles": roles, "channels": channels,
        "supervisor_role": config.get("supervisor_roles", {}).get(gid),
        "promodemo_channel": config.get("promodemo_channels", {}).get(gid),
        "audit_channel": config.get("audit_channels", {}).get(gid),
        "prefix": get_server_prefix(gid),
        "embed_color": "#%06X" % parse_embed_color(embed_settings.get("color")),
        "embed_footer": embed_settings.get("footer", "Supreme Bot"),
        "ticket_title": ticket_settings.get("title", "Support Ticket Center"),
        "ticket_description": ticket_settings.get("description", "Choose a ticket type from the dropdown below to open a private channel with our staff team."),
        "activity_type": activity_settings.get("type", "playing"),
        "activity_text": activity_settings.get("text", ""),
        "can_set_activity": bool(OWNER_ID and str(session["user"]["id"]) == str(OWNER_ID)),
        "economy": get_economy_settings(gid),
    })


async def handle_api_save_settings(request):
    _, guild, error = await web_authorized_guild(request)
    if error:
        return error
    try:
        data = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest):
        return response_json_error("Invalid settings data.")
    if not isinstance(data, dict):
        return response_json_error("Invalid settings data.")

    gid = str(guild.id)
    role_id = str(data.get("supervisor_role", ""))
    if role_id and (not role_id.isdigit() or guild.get_role(int(role_id)) is None):
        return response_json_error("Choose a role from this server.")
    valid_channels = {str(channel.id) for channel in guild.text_channels}
    channel_values = {"promodemo_channels": str(data.get("promodemo_channel", "")), "audit_channels": str(data.get("audit_channel", ""))}
    if any(value and value not in valid_channels for value in channel_values.values()):
        return response_json_error("Choose channels from this server.")

    prefix = str(data.get("prefix", ">"))
    if not 1 <= len(prefix) <= 5 or any(char.isspace() for char in prefix):
        return response_json_error("Prefix must be 1–5 non-space characters.")
    color_text = str(data.get("embed_color", "#5865F2"))
    try:
        color_value = color_text.removeprefix("#")
        if len(color_value) != 6:
            raise ValueError
        int(color_value, 16)
    except ValueError:
        return response_json_error("Choose a valid 6-digit embed color.")
    footer = str(data.get("embed_footer", "Supreme Bot"))[:200]
    ticket_title = str(data.get("ticket_title", "Support Ticket Center")).strip()
    ticket_description = str(data.get("ticket_description", "Choose a ticket type from the dropdown below to open a private channel with our staff team.")).strip()
    if not ticket_title or len(ticket_title) > 100 or len(ticket_description) > 2000:
        return response_json_error("Ticket title must be 1–100 characters and description no more than 2,000.")
    try:
        economy_settings = {
            "daily_min": int(data.get("daily_min", 100)),
            "daily_max": int(data.get("daily_max", 250)),
            "work_min": int(data.get("work_min", 20)),
            "work_max": int(data.get("work_max", 80)),
            "work_cooldown": int(data.get("work_cooldown", 60)),
        }
    except (TypeError, ValueError):
        return response_json_error("Economy settings must be whole numbers.")
    if any(value < 0 or value > 1000000 for key, value in economy_settings.items() if key != "work_cooldown") or not 10 <= economy_settings["work_cooldown"] <= 86400:
        return response_json_error("Rewards must be 0–1,000,000 and cooldown 10–86,400 seconds.")
    if economy_settings["daily_min"] > economy_settings["daily_max"] or economy_settings["work_min"] > economy_settings["work_max"]:
        return response_json_error("Each reward minimum must be less than or equal to its maximum.")
    config.setdefault("prefixes", {})[gid] = prefix
    if role_id: config.setdefault("supervisor_roles", {})[gid] = role_id
    else: config.setdefault("supervisor_roles", {}).pop(gid, None)
    for key, value in channel_values.items():
        if value: config.setdefault(key, {})[gid] = value
        else: config.setdefault(key, {}).pop(gid, None)
    config.setdefault("embed_settings", {})[gid] = {"color": "#" + color_value.upper(), "footer": footer}
    config.setdefault("ticket_settings", {})[gid] = {"title": ticket_title, "description": ticket_description}
    config.setdefault("economy_settings", {})[gid] = economy_settings
    save_config()
    return web.json_response({"ok": True})


async def handle_api_ticket_panel(request):
    _, guild, error = await web_authorized_guild(request)
    if error:
        return error
    try:
        data = await request.json()
        if not isinstance(data, dict):
            return response_json_error("Choose a valid ticket channel.")
        channel_id = int(data.get("channel_id", 0))
    except (json.JSONDecodeError, web.HTTPBadRequest, TypeError, ValueError):
        return response_json_error("Choose a valid ticket channel.")
    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return response_json_error("Choose a text channel from this server.")
    ticket_settings = get_ticket_settings(guild.id)
    panel = discord.Embed(title=ticket_settings["title"], description=ticket_settings["description"], color=discord.Color(parse_embed_color(get_embed_settings(guild.id)["color"])), timestamp=discord.utils.utcnow())
    apply_embed_theme(guild.id, panel)
    try:
        await channel.send(embed=panel, view=TicketSetupView(), allowed_mentions=discord.AllowedMentions.none())
    except discord.Forbidden:
        return response_json_error("Supreme Bot needs permission to send messages and embeds in that channel.", 403)
    except discord.HTTPException:
        logging.exception("Failed to post website ticket panel")
        return response_json_error("Could not post the ticket panel.", 502)
    return web.json_response({"ok": True})


async def handle_api_embed(request):
    session, guild, error = await web_authorized_guild(request)
    if error:
        return error
    try:
        data = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest):
        return response_json_error("Invalid embed data.")
    if not isinstance(data, dict):
        return response_json_error("Invalid embed data.")
    try:
        channel_id = int(data.get("channel_id", 0))
    except (TypeError, ValueError):
        return response_json_error("Choose a channel from this server.")
    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return response_json_error("Choose a text channel from this server.")
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    footer = str(data.get("footer", "")).strip()
    author = str(data.get("author", "")).strip()
    title_url = str(data.get("title_url", "")).strip()
    image_url = str(data.get("image_url", "")).strip()
    thumbnail_url = str(data.get("thumbnail_url", "")).strip()
    if len(title) > 256 or len(description) > 4096 or len(footer) > 200 or len(author) > 256:
        return response_json_error("Embed title, description, or footer is too long.")
    try:
        color_text = str(data.get("color", "#5865F2")).removeprefix("#")
        if len(color_text) != 6: raise ValueError
        color = int(color_text, 16)
    except ValueError:
        return response_json_error("Choose a valid 6-digit color.")
    fields = data.get("fields", [])
    if not isinstance(fields, list) or len(fields) > 25:
        return response_json_error("Embeds can have up to 25 fields.")
    if not title and not description and not fields:
        return response_json_error("Add a title, description, or at least one field.")
    urls = [url for url in (title_url, image_url, thumbnail_url) if url]
    if any(len(url) > 2048 or urllib.parse.urlparse(url).scheme != "https" or not urllib.parse.urlparse(url).netloc for url in urls):
        return response_json_error("Embed links must be valid HTTPS URLs.")
    embed = discord.Embed(title=title or None, description=description or None, color=discord.Color(color), url=title_url or None)
    if author: embed.set_author(name=author)
    if image_url: embed.set_image(url=image_url)
    if thumbnail_url: embed.set_thumbnail(url=thumbnail_url)
    for item in fields:
        if not isinstance(item, dict):
            return response_json_error("Each embed field needs a name and value.")
        name, value = str(item.get("name", "")).strip(), str(item.get("value", "")).strip()
        if not name or not value or len(name) > 256 or len(value) > 1024:
            return response_json_error("Field names must be 1–256 characters and values 1–1,024 characters.")
        embed.add_field(name=name, value=value, inline=bool(item.get("inline", False)))
    theme_footer = get_embed_settings(guild.id).get("footer", "Supreme Bot")
    embed.set_footer(text=footer or theme_footer)
    try:
        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    except discord.Forbidden:
        return response_json_error("Supreme Bot needs permission to send messages and embeds in that channel.", 403)
    except discord.HTTPException:
        logging.exception("Failed to send dashboard embed")
        return response_json_error("Could not send this embed. Check that it fits Discord's embed limits.", 502)
    await audit(guild, f"Dashboard embed sent by {session['user']['id']} to #{channel.name}")
    return web.json_response({"ok": True})


async def handle_api_money(request):
    session, guild, error = await web_authorized_guild(request)
    if error:
        return error
    try:
        data = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest):
        return response_json_error("Invalid economy action.")
    if not isinstance(data, dict):
        return response_json_error("Invalid economy action.")
    user_id = str(data.get("user_id", ""))
    if not user_id.isdigit():
        return response_json_error("Enter a numeric Discord member ID.")
    try:
        member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
    except (discord.NotFound, discord.HTTPException):
        return response_json_error("That member was not found in this server.")
    action = str(data.get("action", ""))
    if action not in {"add", "remove", "set", "reset"}:
        return response_json_error("Choose add, remove, set, or reset.")
    try:
        amount = int(data.get("amount", 0))
    except (TypeError, ValueError):
        return response_json_error("Enter a whole number of coins.")
    if action == "reset":
        amount = 0
    elif amount < (0 if action == "set" else 1) or amount > 1000000000:
        return response_json_error("Amount must be within 0–1,000,000,000 coins.")
    account = economy_account(guild.id, member.id)
    if action == "add": account["balance"] += amount
    elif action == "remove": account["balance"] = max(0, account["balance"] - amount)
    elif action == "set": account["balance"] = amount
    else: account.update({"balance": 0, "last_daily": 0, "last_work": 0})
    save_config()
    await audit(guild, f"Dashboard wallet {action} by {session['user']['id']}: member {member.id}, amount {amount}")
    return web.json_response({"ok": True, "balance": account["balance"]})

async def handle_api_activity(request):
    session = get_web_session(request)
    if not session:
        return response_json_error("Sign in with Discord first.", 401)
    if not OWNER_ID or str(session["user"]["id"]) != str(OWNER_ID):
        return response_json_error("Only the bot owner can change the global activity.", 403)
    try:
        data = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest):
        return response_json_error("Invalid activity settings.")
    if not isinstance(data, dict):
        return response_json_error("Invalid activity settings.")
    activity_type = str(data.get("type", "")).lower()
    text = str(data.get("text", "")).strip()
    if activity_type not in ACTIVITY_TYPES or not 1 <= len(text) <= 128:
        return response_json_error("Choose an activity type and text up to 128 characters.")
    try:
        await apply_bot_activity(activity_type, text)
    except discord.HTTPException:
        return response_json_error("Discord could not apply this activity.", 502)
    config["activity"] = {"type": activity_type, "text": text}
    save_config()
    return web.json_response({"ok": True})

async def start_web_server():
    app = web.Application(client_max_size=64 * 1024)
    app.router.add_get("/", handle_ping)
    app.router.add_get("/dashboard", handle_dashboard)
    app.router.add_get("/login", handle_login)
    app.router.add_get("/oauth/callback", handle_oauth_callback)
    app.router.add_post("/logout", handle_logout)
    app.router.add_get("/api/guilds", handle_api_guilds)
    app.router.add_get("/api/guild/{guild_id}", handle_api_guild)
    app.router.add_post("/api/guild/{guild_id}/settings", handle_api_save_settings)
    app.router.add_post("/api/guild/{guild_id}/ticket-panel", handle_api_ticket_panel)
    app.router.add_post("/api/guild/{guild_id}/embed", handle_api_embed)
    app.router.add_post("/api/activity", handle_api_activity)
    app.router.add_post("/api/guild/{guild_id}/money", handle_api_money)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info("Supreme Bot dashboard started on 0.0.0.0:%s (Bot-Hosting.net SERVER_PORT)", PORT)

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
    "activity": {},
    "prefixes": {},
    "embed_settings": {},
    "ticket_settings": {},
    "economy_settings": {}
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

def get_server_prefix(guild_id):
    return config.get("prefixes", {}).get(str(guild_id), ">") if guild_id else ">"


def get_embed_settings(guild_id):
    defaults = {"color": "#5865F2", "footer": "Supreme Bot"}
    return {**defaults, **config.get("embed_settings", {}).get(str(guild_id), {})}


def get_economy_settings(guild_id):
    defaults = {"daily_min": 100, "daily_max": 250, "work_min": 20, "work_max": 80, "work_cooldown": 60}
    return {**defaults, **config.get("economy_settings", {}).get(str(guild_id), {})}

def get_ticket_settings(guild_id):
    defaults = {"title": f"{EMOJIS['ticket']} Support Ticket Center", "description": "Choose a ticket type from the dropdown below to open a private channel with our staff team."}
    return {**defaults, **config.get("ticket_settings", {}).get(str(guild_id), {})}


def parse_embed_color(value, fallback=0x5865F2):
    try:
        value = str(value).lstrip("#")
        return int(value, 16) if len(value) == 6 else fallback
    except (TypeError, ValueError):
        return fallback


def apply_embed_theme(guild_id, embed):
    settings = get_embed_settings(guild_id)
    embed.color = discord.Color(parse_embed_color(settings.get("color")))
    default_footer = str(settings.get("footer", "")).strip()
    if default_footer:
        previous = getattr(embed.footer, "text", None)
        embed.set_footer(text=f"{previous} • {default_footer}" if previous and previous != default_footer else (previous or default_footer))
    return embed

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

    @discord.ui.select(
        placeholder="Choose a ticket type...",
        min_values=1,
        max_values=1,
        custom_id="ticket_type_select",
        options=[
            discord.SelectOption(label="General Support", value="support", description="Ask the team for help", emoji="🎟️"),
            discord.SelectOption(label="Report a Member", value="report", description="Privately report a server issue", emoji="🚩"),
            discord.SelectOption(label="Other Question", value="other", description="Contact the staff team", emoji="💬"),
        ],
    )
    async def create_ticket(self, interaction: discord.Interaction, select: discord.ui.Select):
        guild = interaction.guild
        member = interaction.user
        ticket_type = select.values[0]
        channel_name = f"ticket-{ticket_type}-{member.id}"

        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"{EMOJIS['error']} You already have this ticket open: {existing_channel.mention}", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        supervisor_role_id = guild_setting("supervisor_roles", guild.id)
        if supervisor_role_id:
            sup_role = guild.get_role(int(supervisor_role_id))
            if sup_role:
                overwrites[sup_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        staff_team_role = discord.utils.find(lambda r: "staff team" in r.name.lower(), guild.roles)
        if staff_team_role:
            overwrites[staff_team_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        category = discord.utils.get(guild.categories, name="Support Tickets")
        if not category:
            category = await guild.create_category("Support Tickets")

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"{ticket_type.title()} ticket for {member} ({member.id})"
        )

        embed = discord.Embed(
            title=f"{EMOJIS['ticket']} {ticket_type.title()} Ticket",
            description=f"Hello {member.mention}! Support staff will be with you shortly.\nUse the button below when you are ready to close this ticket.",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Supreme • Ticket System")
        apply_embed_theme(guild.id, embed)

        await channel.send(embed=embed, view=TicketCloseView())
        await interaction.followup.send(f"{EMOJIS['success']} Your {ticket_type} ticket is ready: {channel.mention}", ephemeral=True)
        await audit(guild, f"{ticket_type.title()} ticket created by {member} ({member.id}) | Channel: {channel.name}")

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
    apply_embed_theme(guild.id, embed)

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
            await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} No rank ladder configured. Add roles using `{get_server_prefix(ctx.guild.id)}ranks add @role`", color=discord.Color.orange()))
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
            await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} No rank ladder configured. Add roles using `{get_server_prefix(ctx.guild.id)}ranks add @role`", color=discord.Color.orange()))
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
        name=f"{EMOJIS['promo']} `{get_server_prefix(ctx.guild.id)}promo @member [@role]`",
        value=(
            f"{EMOJIS['bullet']} Promotes a staff member.\n"
            f"{EMOJIS['bullet']} **Auto Ladder:** If no role is given, advances them to the next step up."
        ),
        inline=False
    )

    embed.add_field(
        name=f"{EMOJIS['demo']} `{get_server_prefix(ctx.guild.id)}demo @member [@role]`",
        value=(
            f"{EMOJIS['bullet']} Demotes a staff member.\n"
            f"{EMOJIS['bullet']} **Auto Ladder:** If no role is given, strips their highest rank to drop them down."
        ),
        inline=False
    )

    embed.add_field(
        name=f"{EMOJIS['gear']} `{get_server_prefix(ctx.guild.id)}role @member @role`",
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
            f"{EMOJIS['bullet']} `{get_server_prefix(ctx.guild.id)}kick @member [reason]` — Kicks a disruptive user from the server.\n"
            f"{EMOJIS['bullet']} `{get_server_prefix(ctx.guild.id)}ban @member [reason]` — Permanently bans a rule-breaker.\n"
            f"{EMOJIS['bullet']} `{get_server_prefix(ctx.guild.id)}mute @member [reason]` — Times out a user for 10 minutes.\n"
            f"{EMOJIS['bullet']} `{get_server_prefix(ctx.guild.id)}clear [amount]` — Purges recent chat messages cleanly."
        ),
        inline=False
    )

    embed.add_field(
        name=f"{EMOJIS['user']} Utility & Information",
        value=(
            f"{EMOJIS['bullet']} `{get_server_prefix(ctx.guild.id)}userinfo [@member]` — Checks account creation, join dates, and roles.\n"
            f"{EMOJIS['bullet']} `{get_server_prefix(ctx.guild.id)}avatar [@member]` — Views high-resolution profile pictures."
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

    ticket_settings = get_ticket_settings(ctx.guild.id)
    embed = discord.Embed(title=ticket_settings["title"], description=ticket_settings["description"], color=discord.Color(parse_embed_color(get_embed_settings(ctx.guild.id)["color"])), timestamp=discord.utils.utcnow())
    apply_embed_theme(ctx.guild.id, embed)

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
    economy_settings = get_economy_settings(ctx.guild.id)
    reward = random.randint(int(economy_settings["daily_min"]), int(economy_settings["daily_max"]))
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
    economy_settings = get_economy_settings(ctx.guild.id)
    remaining = int(economy_settings["work_cooldown"]) - (int(time.time()) - int(account.get("last_work", 0)))
    if remaining > 0:
        await ctx.reply(embed=economy_embed(f"Catch your breath! You can work again in **{remaining}s**."))
        return
    reward = random.randint(int(economy_settings["work_min"]), int(economy_settings["work_max"]))
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
        await ctx.reply(embed=economy_embed(f"No wallets yet. Start with `{get_server_prefix(ctx.guild.id)}daily`!"))
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
    ladder_str = " -> ".join([f"<@&{r_id}>" for r_id in ladder]) if ladder else f"Not configured. Use `{get_server_prefix(ctx.guild.id)}ranks add @role`"
    
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
    
    ladder_str = " -> ".join([f"<@&{r_id}>" for r_id in ladder]) if ladder else f"Not configured (`{get_server_prefix(ctx.guild.id)}ranks add @role`)"

    embed = discord.Embed(
        title=f"{EMOJIS['gear']} Supreme • Server Settings",
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name=f"{EMOJIS['shield']} Supervisor Role",
        value=supervisor.mention if supervisor else f"Not configured (`{get_server_prefix(ctx.guild.id)}setstaffsupervisor @role`)",
        inline=False
    )
    embed.add_field(
        name=f"{EMOJIS['announcement']} Announcement Channel",
        value=promo_channel.mention if promo_channel else f"Not configured (`{get_server_prefix(ctx.guild.id)}setpromodemo #channel`)",
        inline=False
    )
    embed.add_field(
        name=f"{EMOJIS['audit']} Audit Log Channel",
        value=audit_channel.mention if audit_channel else f"Not configured (`{get_server_prefix(ctx.guild.id)}setaudit #channel`)",
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
    prefix = get_server_prefix(ctx.guild.id if ctx.guild else None)
    embed = discord.Embed(title=f"{EMOJIS['gear']} Supreme • Command Center", description="Here are all available command modules:", color=discord.Color.blurple())
    embed.add_field(name=f"{EMOJIS['shield']} Staff & Management", value=f"`{prefix}promo`, `{prefix}demo`, `{prefix}super`, `{prefix}superintro`, `{prefix}staffintro`, `{prefix}staff`, `{prefix}role`, `{prefix}steal`", inline=False)
    embed.add_field(name=f"{EMOJIS['warning']} Moderation", value=f"`{prefix}kick`, `{prefix}ban`, `{prefix}clear`, `{prefix}mute`", inline=False)
    embed.add_field(name=f"{EMOJIS['money']} Economy", value=f"`{prefix}balance [@member]`, `{prefix}daily`, `{prefix}work`, `{prefix}pay @member amount`, `{prefix}leaderboard`", inline=False)
    embed.add_field(name=f"{EMOJIS['money']} Economy Admin (Owner/Supervisor)", value=f"`{prefix}addmoney @member amount`, `{prefix}removemoney @member amount`, `{prefix}setmoney @member amount`, `{prefix}resetmoney [@member]`", inline=False)
    embed.add_field(name=f"{EMOJIS['ticket']} Support & Tickets", value=f"`{prefix}ticketsetup` (posts a ticket-type dropdown)", inline=False)
    embed.add_field(name=f"{EMOJIS['user']} Utility & Info", value=f"`{prefix}ping`, `{prefix}serverinfo`, `{prefix}userinfo`, `{prefix}avatar`", inline=False)
    embed.add_field(name=f"{EMOJIS['success']} Fun & Games", value=f"`{prefix}coinflip`, `{prefix}roll`", inline=False)
    embed.add_field(name=f"{EMOJIS['gear']} Setup", value=f"`{prefix}ranks add @role`, `{prefix}ranks clear`, `{prefix}setstaffsupervisor`, `{prefix}setpromodemo`, `{prefix}setaudit`, `{prefix}staffsettings`, `{prefix}addextraowner @member`, `{prefix}removextraowner @member`, `{prefix}setactivity <playing|streaming|listening|watching|competing> <text>`", inline=False)
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






















