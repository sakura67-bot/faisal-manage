import io
import os
import re
import json
import logging
import random
import asyncio
import secrets
import sys
import time
import urllib.parse
import aiohttp
import discord
from typing import Literal
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
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://7n27562b55.apps.bot-hosting.cloud").rstrip("/")
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
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MEMBERS RUSH Dashboard</title>
<style>:root{color-scheme:dark;--bg:#08160b;--card:#112a17;--line:#295332;--accent:#8bffb4;--accent2:#65e2a4;--text:#f5fff8;--muted:#aaceb2;--shadow:0 24px 70px #0008}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at 10% -10%,#358b5488,transparent 35%),radial-gradient(ellipse at 100% 20%,#14774670,transparent 30%),var(--bg);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--text);min-height:100vh}body:before{content:'';position:fixed;inset:0;pointer-events:none;opacity:.16;background-image:radial-gradient(#bdffd3 .6px,transparent .6px);background-size:24px 24px;mask-image:linear-gradient(to bottom,#000,transparent 80%)}.wrap{position:relative;max-width:1120px;margin:0 auto;padding:32px 22px 60px}.bar{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;padding:14px 18px;background:#0e2513b8;border:1px solid #9cffbd27;border-radius:18px;backdrop-filter:blur(16px);box-shadow:0 12px 36px #0003}.tag{color:#c6ffda;font-weight:800;letter-spacing:.14em;text-transform:uppercase;font-size:11px}.bar .small{margin-top:3px}.hero{position:relative;overflow:hidden;margin:24px 0 20px;padding:36px 34px;border:1px solid #aaffc733;border-radius:26px;background:linear-gradient(120deg,#1d4d2edd,#112b17dd 65%,#123d28dd);box-shadow:var(--shadow)}.hero:after{content:'✦';position:absolute;right:7%;top:-65px;font-size:230px;line-height:1;color:#d0ffe00b;transform:rotate(12deg);pointer-events:none}.hero h1{max-width:720px;font-size:clamp(34px,6vw,58px);line-height:1.05;letter-spacing:-.045em;margin:11px 0 14px}.hero p{max-width:700px;margin:0;color:#c3dfca;font-size:16px}.hero:before{content:'CONTROL CENTER  /  YOUR SERVER';display:inline-flex;color:#aaf7d0;font-size:10px;font-weight:800;letter-spacing:.16em}.card{position:relative;background:linear-gradient(145deg,#15321bf2,#102615f5);border:1px solid #c5ffd51c;border-radius:20px;padding:24px;margin:18px 0;box-shadow:0 18px 50px #020b0475;transition:transform .22s,border-color .22s,box-shadow .22s}.card:hover{border-color:#8bffb450;box-shadow:0 22px 60px #020b0499,0 0 28px #70ffa20d}.card h2{display:flex;align-items:center;gap:10px;margin:0 0 4px;font-size:21px;letter-spacing:-.02em}.card h2:before{content:'';width:4px;height:22px;border-radius:5px;background:linear-gradient(var(--accent),var(--accent2));box-shadow:0 0 14px #8bffb488}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px;margin-top:16px}.field{display:flex;flex-direction:column;gap:8px;margin:9px 0}label{font-size:13px;font-weight:700;color:#e3f5e8}input,select,textarea{background:#0b2010;color:var(--text);border:1px solid #355e3e;border-radius:12px;padding:12px 14px;font:inherit;width:100%;outline:0;transition:border-color .18s,box-shadow .18s,background .18s}input:focus,select:focus,textarea:focus{border-color:#8bffb4;box-shadow:0 0 0 3px #8bffb424;background:#102a16}input[type=color]{height:47px;padding:5px;cursor:pointer}textarea{min-height:115px;resize:vertical}button,.button{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:linear-gradient(120deg,#9affbe,#72ef9e);color:#102618;border:1px solid #cdffdf55;border-radius:12px;padding:12px 18px;font:inherit;font-weight:800;text-decoration:none;cursor:pointer;margin:7px 8px 0 0;box-shadow:0 8px 24px #70e99c33;transition:transform .18s,filter .18s,box-shadow .18s}button:hover,.button:hover{transform:translateY(-2px);filter:brightness(1.08);box-shadow:0 12px 30px #70e99c55}button:active,.button:active{transform:translateY(0)}button.secondary{background:#204328;color:#e7ffed;border-color:#6a957355;box-shadow:none}.small{font-size:12px;color:var(--muted)}.hidden{display:none}.row{display:flex;gap:10px;align-items:center}.status{min-height:26px;color:#a7f4d5;margin-top:12px}.preview{white-space:pre-wrap;background:linear-gradient(110deg,#0b2010,#112a17);border:1px solid #295332;border-left:4px solid var(--accent);padding:16px;border-radius:12px;min-height:76px;color:#e2f5e7;margin-top:12px}.card>p{color:var(--muted);line-height:1.65;margin:4px 0 10px}.card .field .small{line-height:1.5}@media(max-width:700px){.grid{grid-template-columns:1fr}.wrap{padding:16px 12px 38px}.card{padding:18px;border-radius:16px}.hero{padding:28px 22px;border-radius:20px}.hero:after{right:-8%;top:-25px;font-size:150px}.bar{padding:12px 14px}}.dash-nav{position:sticky;top:10px;z-index:5;display:flex;gap:8px;flex-wrap:wrap;padding:10px;margin:14px 0 20px;background:#0c2011dd;border:1px solid #adffc824;border-radius:16px;backdrop-filter:blur(16px)}.dash-nav a{color:#d9eedf;text-decoration:none;font-size:13px;font-weight:750;padding:9px 13px;border-radius:10px;transition:.18s}.dash-nav a:hover{color:#fff;background:#8bffb429}.card[id]{scroll-margin-top:90px}</style></head><body><main class="wrap"><div class="bar"><div><div class="tag">MEMBERS RUSH • Bot-Hosting.net</div><div class="small">Server dashboard</div></div><button class="secondary" onclick="logout()">Log out</button></div>
<section class="hero"><h1>Bot control panel</h1><p>One beautiful control center for your server setup, embeds, tickets, and staff tools. Dashboard access is limited to the bot owner and trusted extra owners.</p></section>
<nav class="dash-nav" aria-label="Dashboard sections"><a href="#settings">⚙️ Server</a><a href="#embedCard">✦ Embeds</a></nav>
<section class="card"><div class="field"><label for="guild">Discord server</label><select id="guild"></select></div><div id="settings" class="hidden"><h2>Server settings</h2><p class="small">Prefix, staff destinations, embed appearance, and ticket panel content are saved per server.</p><div class="grid">
<div class="field"><label for="prefix">Command prefix</label><input id="prefix" maxlength="5" value=">"><span class="small">Example: `>` or `!`</span></div>
<div class="field"><label for="supervisor">Supervisor role</label><select id="supervisor"></select></div>
<div class="field"><label for="promoChannel">Promotion channel</label><select id="promoChannel"></select></div><div class="field"><label for="demoChannel">Demotion channel</label><select id="demoChannel"></select></div><div class="field"><label for="audit">Logs channel</label><select id="audit"></select></div>
<div class="field"><label for="embedColor">Default embed color</label><input id="embedColor" type="color" value="#2ecc71"></div><div class="field"><label for="footer">Default embed footer</label><input id="footer" maxlength="200" placeholder="MEMBERS RUSH"></div>
<div class="field"><label for="ticketTitle">Ticket panel title</label><input id="ticketTitle" maxlength="100"></div><div class="field"><label for="ticketChannel">Ticket panel channel</label><select id="ticketChannel"></select></div>
<div class="field"><label for="ticketDescription">Ticket panel description</label><textarea id="ticketDescription" maxlength="2000"></textarea></div>

</div><button onclick="saveSettings()">Save server settings</button><button class="secondary" onclick="postPanel()">Post ticket dropdown</button><div id="settingsStatus" class="status"></div></div><div id="empty" class="small hidden">No eligible servers found. Ask the bot owner to add you with >addextraowner if you need dashboard access.</div></section>
<section id="embedCard" class="card hidden"><h2>Embed builder</h2><p class="small">Create and send a custom embed to a channel. Field rows use `name | value | inline`; use `true` or `false` for inline.</p><div class="grid"><div class="field"><label for="embedChannel">Post in</label><select id="embedChannel"></select></div><div class="field"><label for="customColor">Embed color</label><input id="customColor" type="color" value="#2ecc71"></div><div class="field"><label for="customTitle">Title</label><input id="customTitle" maxlength="256" placeholder="Announcement"></div><div class="field"><label for="customFooter">Footer</label><input id="customFooter" maxlength="200" placeholder="Optional footer"></div>
<div class="field"><label for="customAuthor">Author label</label><input id="customAuthor" maxlength="256" placeholder="Optional author"></div><div class="field"><label for="customUrl">Title link (HTTPS URL)</label><input id="customUrl" maxlength="2048" placeholder="https://example.com"></div><div class="field"><label for="customImage">Image URL (HTTPS)</label><input id="customImage" maxlength="2048" placeholder="https://example.com/image.png"></div><div class="field"><label for="customThumb">Thumbnail URL (HTTPS)</label><input id="customThumb" maxlength="2048" placeholder="https://example.com/thumb.png"></div><div class="field"><label for="customDescription">Description</label><textarea id="customDescription" maxlength="4000" placeholder="Write your embed message"></textarea></div><div class="field"><label for="customFields">Fields (one per line)</label><textarea id="customFields" placeholder="Rules | Be kind to everyone | false&#10;Need help? | Open a ticket below | true"></textarea></div></div><div class="preview" id="preview">Embed preview will appear here.</div><button onclick="sendEmbed()">Send embed</button><div id="embedStatus" class="status"></div></section>
<section id="activityCard" class="card hidden"><h2>Bot activity</h2><p class="small">This changes the bot-wide Discord presence. Only the bot owner can save it.</p><div class="grid"><div class="field"><label for="activityType">Activity</label><select id="activityType"><option>playing</option><option>streaming</option><option>listening</option><option>watching</option><option>competing</option></select></div><div class="field"><label for="activityText">Activity text</label><input id="activityText" maxlength="128" placeholder="MEMBERS RUSH"></div></div><button class="secondary" onclick="saveActivity()">Save activity</button><div id="activityStatus" class="status"></div></section>
<p class="small">The website runs inside this bot deployment. Activate a Bot-Hosting.net HTTPS subdomain and set the Discord OAuth redirect URL to `/oauth/callback`.</p></main>
<script>
const guildSelect=document.getElementById('guild'),settings=document.getElementById('settings'),statusBox=document.getElementById('settingsStatus');
async function api(path,options={}){const response=await fetch(path,{credentials:'same-origin',headers:{'Content-Type':'application/json',...(options.headers||{})},...options});if(response.status===401){location.href='/login';throw new Error('Please sign in again.')}const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');return data}
function fill(id,items,selected,label){const el=document.getElementById(id);el.replaceChildren(new Option(label,''));for(const item of items)el.add(new Option(item.name,item.id));if(selected)el.value=String(selected)}
async function loadGuilds(){try{const data=await api('/api/guilds');if(!data.guilds.length){document.getElementById('empty').classList.remove('hidden');return}for(const g of data.guilds)guildSelect.add(new Option(g.name+" · "+g.id,g.id));await loadConfig()}catch(e){statusBox.textContent=e.message}}
async function loadConfig(){try{const d=await api('/api/guild/'+guildSelect.value);fill('supervisor',d.roles,d.supervisor_role,'No supervisor role');fill('promoChannel',d.channels,d.promo_channel,'Not set');fill('demoChannel',d.channels,d.demo_channel,'Not set');fill('audit',d.channels,d.audit_channel,'Not set');fill('ticketChannel',d.channels,null,'Choose a channel');fill('embedChannel',d.channels,null,'Choose a channel');document.getElementById('prefix').value=d.prefix;document.getElementById('embedColor').value=d.embed_color;document.getElementById('footer').value=d.embed_footer;document.getElementById('ticketTitle').value=d.ticket_title;document.getElementById('ticketDescription').value=d.ticket_description;document.getElementById('activityType').value=d.activity_type||'playing';document.getElementById('activityText').value=d.activity_text||'';document.getElementById('activityCard').classList.toggle('hidden',!d.can_set_activity);settings.classList.remove('hidden');document.getElementById('embedCard').classList.remove('hidden');document.getElementById('empty').classList.add('hidden')}catch(e){statusBox.textContent=e.message}}
guildSelect.addEventListener('change',loadConfig);
async function saveSettings(){statusBox.textContent='Saving…';try{await api('/api/guild/'+guildSelect.value+'/settings',{method:'POST',body:JSON.stringify({prefix:document.getElementById('prefix').value,supervisor_role:document.getElementById('supervisor').value,promo_channel:document.getElementById('promoChannel').value,demo_channel:document.getElementById('demoChannel').value,audit_channel:document.getElementById('audit').value,embed_color:document.getElementById('embedColor').value,embed_footer:document.getElementById('footer').value,ticket_title:document.getElementById('ticketTitle').value,ticket_description:document.getElementById('ticketDescription').value})});statusBox.textContent='Settings saved.'}catch(e){statusBox.textContent=e.message}}
async function postPanel(){const channel=document.getElementById('ticketChannel').value;if(!channel){statusBox.textContent='Choose a ticket panel channel first.';return}statusBox.textContent='Posting…';try{await api('/api/guild/'+guildSelect.value+'/ticket-panel',{method:'POST',body:JSON.stringify({channel_id:channel})});statusBox.textContent='Ticket dropdown posted.'}catch(e){statusBox.textContent=e.message}}
function updatePreview(){const title=document.getElementById('customTitle').value,description=document.getElementById('customDescription').value;document.getElementById('preview').textContent=(title?'◆ '+title+'\n':'')+(description||'Embed preview will appear here.');document.getElementById('preview').style.borderColor=document.getElementById('customColor').value}
['customTitle','customDescription','customColor'].forEach(id=>document.getElementById(id).addEventListener('input',updatePreview));
async function sendEmbed(){const channel=document.getElementById('embedChannel').value;if(!channel){document.getElementById('embedStatus').textContent='Choose a channel first.';return}const fields=document.getElementById('customFields').value.split('\n').map(x=>x.trim()).filter(Boolean).map(line=>{const p=line.split('|');return{name:(p[0]||'').trim(),value:(p[1]||'').trim(),inline:(p[2]||'').trim().toLowerCase()==='true'}});const box=document.getElementById('embedStatus');box.textContent='Sending…';try{await api('/api/guild/'+guildSelect.value+'/embed',{method:'POST',body:JSON.stringify({channel_id:channel,title:document.getElementById('customTitle').value,description:document.getElementById('customDescription').value,color:document.getElementById('customColor').value,footer:document.getElementById('customFooter').value,author:document.getElementById('customAuthor').value,title_url:document.getElementById('customUrl').value,image_url:document.getElementById('customImage').value,thumbnail_url:document.getElementById('customThumb').value,fields})});box.textContent='Embed sent.'}catch(e){box.textContent=e.message}}
async function logout(){await fetch('/logout',{method:'POST',credentials:'same-origin'});location.href='/'}loadGuilds();
</script></body></html>"""
LANDING_HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MEMBERS RUSH</title><style>*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 15% 5%,#429c62 0,transparent 40%),radial-gradient(ellipse at 90% 90%,#10663b 0,transparent 38%),#08160b;color:#f5fff8;font:16px/1.6 Inter,system-ui,sans-serif;min-height:100vh;display:grid;place-items:center;padding:22px}.card{position:relative;overflow:hidden;width:min(100%,700px);margin:20px;padding:clamp(28px,6vw,56px);background:linear-gradient(140deg,#1c4025ed,#102b16ec 72%,#123524ed);border:1px solid #aaffc742;border-radius:28px;box-shadow:0 30px 100px #0009,0 0 55px #7dffab1a;backdrop-filter:blur(18px)}.card:after{content:'✦';position:absolute;right:5%;top:-100px;color:#dcffe80b;font-size:300px;pointer-events:none}.card>div{position:relative;z-index:1;color:#b8ffd1;font-size:11px;font-weight:850;letter-spacing:.16em}.card h1{position:relative;z-index:1;font-size:clamp(38px,7vw,64px);line-height:1.02;letter-spacing:-.05em;margin:22px 0 16px}.card p{position:relative;z-index:1;color:#bddcc4;line-height:1.75}.button{position:relative;z-index:1;display:inline-flex;background:linear-gradient(120deg,#9affbe,#72ef9e);color:#102618;padding:14px 21px;border:1px solid #cdffdf55;border-radius:13px;font-weight:850;text-decoration:none;box-shadow:0 10px 30px #70e99c44;transition:.2s}.button:hover{transform:translateY(-2px);filter:brightness(1.08)}.note{font-size:13px;margin-top:24px;padding-top:17px;border-top:1px solid #ffffff19}</style></head><body><main class="card"><div>SUPREME BOT • DASHBOARD</div><h1>Configure your server</h1><p>Sign in with Discord to manage server settings. Only the bot owner and trusted extra owners can enter the dashboard.</p><a class="button" href="/login">Continue with Discord</a><p class="note">The bot must already be invited to your server. Set DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, and DISCORD_REDIRECT_URI in the hosting environment to enable sign-in.</p></main></body></html>"""


def get_web_session(request):
    session_id = request.cookies.get("egg_session")
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
    extra_owner = str(session["user"]["id"]) in {str(uid) for uid in config.get("extra_owners", {}).get(str(guild_id), [])}
    bot_owner = int(OWNER_ID) > 0 and str(session["user"]["id"]) == str(OWNER_ID)
    return bot_owner or extra_owner


def response_json_error(message, status=400):
    return web.json_response({"error": message}, status=status)


async def handle_ping(request):
    if get_web_session(request):
        raise web.HTTPFound("/dashboard")
    return web.Response(text=LANDING_HTML, content_type="text/html")


async def handle_dashboard(request):
    session = get_web_session(request)
    if not session:
        raise web.HTTPFound("/")
    if not any(web_user_can_manage(session, info.get("id")) for info in session.get("guilds", [])):
        return web.Response(text="Dashboard access is limited to the bot owner and trusted extra owners.", status=403)
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")


async def handle_login(request):
    if not (DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET and DISCORD_REDIRECT_URI):
        return web.Response(text="Set DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, and DISCORD_REDIRECT_URI in the hosting environment first.", status=503)
    state = secrets.token_urlsafe(24)
    params = urllib.parse.urlencode({"client_id": DISCORD_CLIENT_ID, "redirect_uri": DISCORD_REDIRECT_URI, "response_type": "code", "scope": "identify guilds", "state": state, "prompt": "consent"})
    response = web.HTTPFound("https://discord.com/oauth2/authorize?" + params)
    response.set_cookie("egg_oauth_state", state, max_age=600, httponly=True, secure=True, samesite="Lax")
    raise response


async def handle_oauth_callback(request):
    state = request.query.get("state", "")
    if not state or state != request.cookies.get("egg_oauth_state"):
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

    candidate_session = {"user": {"id": str(user["id"])}, "guilds": guilds}
    if not any(web_user_can_manage(candidate_session, info.get("id")) for info in guilds):
        return web.Response(text="Dashboard access is limited to the bot owner and trusted extra owners.", status=403)

    session_id = secrets.token_urlsafe(32)
    WEB_SESSIONS[session_id] = {"user": {"id": str(user["id"]), "username": user.get("username", "Discord user")}, "guilds": guilds, "expires": time.time() + 12 * 60 * 60}
    result = web.HTTPFound("/dashboard")
    result.set_cookie("egg_session", session_id, max_age=12 * 60 * 60, httponly=True, secure=True, samesite="Lax")
    result.del_cookie("egg_oauth_state")
    raise result


async def handle_logout(request):
    session_id = request.cookies.get("egg_session")
    if session_id:
        WEB_SESSIONS.pop(session_id, None)
    response = web.json_response({"ok": True})
    response.del_cookie("egg_session")
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
        return None, None, response_json_error("MEMBERS RUSH is not in that server.", 404)
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
        "promo_channel": config.get("promo_channels", {}).get(gid) or config.get("promodemo_channels", {}).get(gid),
        "demo_channel": config.get("demo_channels", {}).get(gid) or config.get("promodemo_channels", {}).get(gid),
        "audit_channel": config.get("audit_channels", {}).get(gid),
        "prefix": get_server_prefix(gid),
        "embed_color": "#%06X" % parse_embed_color(embed_settings.get("color")),
        "embed_footer": embed_settings.get("footer", "MEMBERS RUSH"),
        "ticket_title": ticket_settings.get("title", "Support Ticket Center"),
        "ticket_description": ticket_settings.get("description", "Choose a ticket type from the dropdown below to open a private channel with our staff team."),
        "activity_type": activity_settings.get("type", "playing"),
        "activity_text": activity_settings.get("text", ""),
        "can_set_activity": bool(OWNER_ID and str(session["user"]["id"]) == str(OWNER_ID)),
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
    channel_values = {
        "promo_channels": str(data.get("promo_channel", "")),
        "demo_channels": str(data.get("demo_channel", "")),
        "audit_channels": str(data.get("audit_channel", "")),
    }
    if any(value and value not in valid_channels for value in channel_values.values()):
        return response_json_error("Choose channels from this server.")

    prefix = str(data.get("prefix", ">"))
    if not 1 <= len(prefix) <= 5 or any(char.isspace() for char in prefix):
        return response_json_error("Prefix must be 1–5 non-space characters.")
    color_text = str(data.get("embed_color", "#2ECC71"))
    try:
        color_value = color_text.removeprefix("#")
        if len(color_value) != 6:
            raise ValueError
        int(color_value, 16)
    except ValueError:
        return response_json_error("Choose a valid 6-digit embed color.")
    footer = str(data.get("embed_footer", "MEMBERS RUSH"))[:200]
    ticket_title = str(data.get("ticket_title", "Support Ticket Center")).strip()
    ticket_description = str(data.get("ticket_description", "Choose a ticket type from the dropdown below to open a private channel with our staff team.")).strip()
    if not ticket_title or len(ticket_title) > 100 or len(ticket_description) > 2000:
        return response_json_error("Ticket title must be 1–100 characters and description no more than 2,000.")
    config.setdefault("prefixes", {})[gid] = prefix
    if role_id: config.setdefault("supervisor_roles", {})[gid] = role_id
    else: config.setdefault("supervisor_roles", {}).pop(gid, None)
    for key, value in channel_values.items():
        if value: config.setdefault(key, {})[gid] = value
        else: config.setdefault(key, {}).pop(gid, None)
    config.setdefault("embed_settings", {})[gid] = {"color": "#" + color_value.upper(), "footer": footer}
    config.setdefault("ticket_settings", {})[gid] = {"title": ticket_title, "description": ticket_description}
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
        return response_json_error("MEMBERS RUSH needs permission to send messages and embeds in that channel.", 403)
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
        color_text = str(data.get("color", "#2ECC71")).removeprefix("#")
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
    theme_footer = get_embed_settings(guild.id).get("footer", "MEMBERS RUSH")
    embed.set_footer(text=footer or theme_footer)
    try:
        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    except discord.Forbidden:
        return response_json_error("MEMBERS RUSH needs permission to send messages and embeds in that channel.", 403)
    except discord.HTTPException:
        logging.exception("Failed to send dashboard embed")
        return response_json_error("Could not send this embed. Check that it fits Discord's embed limits.", 502)
    await audit(guild, f"Dashboard embed sent by {session['user']['id']} to #{channel.name}")
    return web.json_response({"ok": True})


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
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info("MEMBERS RUSH dashboard started on 0.0.0.0:%s (Bot-Hosting.net SERVER_PORT)", PORT)

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
    "ticket": "<:ticket:1560983848345665637>"
}

EMOJI_SOURCES = dict(EMOJIS)

async def install_application_emojis():
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
    "promo_channels": {},
    "demo_channels": {},
    "audit_channels": {},
    "economy": {},
    "economy_settings": {},
    "economy_shop": {},
    "economy_lotteries": {},
    "economy_market": {},
    "economy_gangs": {},
    "staff_stats": {},
    "rank_ladders": {},
    "staff_limits": {},
    "extra_owners": {},
    "activity": {},
    "prefixes": {},
    "embed_settings": {},
    "ticket_settings": {},
    "blacklists": {},
    "disabled_guilds": {},
    "ai_tasks": {},
    "ai_channels": {},
    "levels": {},
    "level_settings": {},
    "level_roles": {},
    "log_settings": {}
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
        return True
    except OSError:
        logging.exception("Could not save configuration")
        return False


CONFIG_DIRTY = False
INVITE_CACHE = {}


def mark_config_dirty():
    global CONFIG_DIRTY
    CONFIG_DIRTY = True


def staff_stat_bucket(guild_id, user_id):
    return config.setdefault("staff_stats", {}).setdefault(str(guild_id), {}).setdefault(
        str(user_id), {"invites": 0, "messages": 0, "moderation": 0})


def add_staff_stat(guild_id, user_id, key, amount=1):
    bucket = staff_stat_bucket(guild_id, user_id)
    bucket[key] = int(bucket.get(key, 0)) + amount
    mark_config_dirty()


def user_is_staff_member(member, guild):
    extras = {str(uid) for uid in config.get("extra_owners", {}).get(str(guild.id), [])}
    if member.id in {OWNER_ID, guild.owner_id} or str(member.id) in extras:
        return True
    sid = config.get("supervisor_roles", {}).get(str(guild.id))
    if sid and any(r.id == int(sid) for r in member.roles):
        return True
    return any(any(t in r.name.lower() for t in ("staff", "trial", "mod", "supervisor"))
               for r in member.roles)


async def refresh_invite_cache(guild):
    try:
        invites = await guild.invites()
        INVITE_CACHE[guild.id] = {i.code: i.uses or 0 for i in invites}
    except (discord.Forbidden, discord.HTTPException):
        logging.info("Invite tracking unavailable for guild %s; grant Manage Server.", guild.id)


async def config_autosave_loop():
    global CONFIG_DIRTY
    while True:
        await asyncio.sleep(30)
        if CONFIG_DIRTY:
            CONFIG_DIRTY = False
            save_config()


def get_server_prefix(guild_id):
    return config.get("prefixes", {}).get(str(guild_id), ">") if guild_id else ">"


def get_embed_settings(guild_id):
    defaults = {"color": "#2ECC71", "footer": "MEMBERS RUSH"}
    return {**defaults, **config.get("embed_settings", {}).get(str(guild_id), {})}


def get_ticket_settings(guild_id):
    defaults = {"title": f"{EMOJIS['announcement']} Support Ticket Center", "description": "Choose a ticket type from the dropdown below to open a private channel with our staff team."}
    return {**defaults, **config.get("ticket_settings", {}).get(str(guild_id), {})}


def parse_embed_color(value, fallback=0x2ECC71):
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


class MemberBlacklisted(commands.CheckFailure):
    pass


class GuildCommandsDisabled(commands.CheckFailure):
    pass


@bot.check
async def global_command_access_check(ctx):
    if ctx.guild is None:
        return True
    guild_id = str(ctx.guild.id)
    blacklisted = config.get("blacklists", {}).get(guild_id, [])
    if str(ctx.author.id) in {str(user_id) for user_id in blacklisted}:
        raise MemberBlacklisted()
    control_commands = {"blacklist", "unblacklist", "disable", "enable", "shutdown", "restart"}
    if ctx.command and ctx.command.name in control_commands:
        return True
    if config.get("disabled_guilds", {}).get(guild_id, False):
        raise GuildCommandsDisabled()
    return True


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
# LOGGING SYSTEM
# =========================

LOG_CATEGORIES = {
    "messages": "Message edits & deletes",
    "members": "Joins, leaves & member updates",
    "voice": "Voice activity",
    "server": "Channel & role changes",
    "moderation": "Moderation & audit actions",
    "tickets": "Ticket activity",
}
LOG_SUPPRESS = {}


def suppress_log(guild_id, user_id, action):
    LOG_SUPPRESS[(guild_id, user_id, action)] = time.monotonic()


def log_suppressed(guild_id, user_id, *actions):
    now = time.monotonic()
    return any(now - LOG_SUPPRESS.get((guild_id, user_id, action), -999) < 15 for action in actions)


def log_category_enabled(guild_id, category):
    return bool(config.get("log_settings", {}).get(str(guild_id), {}).get(category, True))


def get_log_channel(guild):
    channel_id = guild_setting("audit_channels", guild.id)
    if not channel_id:
        return None
    return guild.get_channel(int(channel_id))


async def send_log(guild, category, title, description=None, *, fields=None, color=None, user=None, file=None):
    if guild is None or not log_category_enabled(guild.id, category):
        return None
    channel = get_log_channel(guild)
    if channel is None:
        return None
    embed = discord.Embed(title=title, description=(description or None), color=color or discord.Color(0x2ECC71), timestamp=discord.utils.utcnow())
    for name, value, inline in fields or []:
        embed.add_field(name=name, value=(str(value)[:1024] or "\u200b"), inline=inline)
    if user is not None:
        embed.set_author(name=f"{user} ({user.id})", icon_url=user.display_avatar.url)
    embed.set_footer(text="MEMBERS RUSH \u2022 Logs")
    kwargs = {"embed": embed, "allowed_mentions": discord.AllowedMentions.none()}
    if file is not None:
        kwargs["file"] = file
    try:
        return await channel.send(**kwargs)
    except discord.HTTPException:
        logging.exception("Failed to send log")
        return None


async def audit(guild, message):
    await send_log(guild, "moderation", f"{EMOJIS['audit']} Audit Log", str(message)[:4000])


# =========================
# TICKET SYSTEM & AI TICKET ASSISTANT
# =========================

TICKET_TYPES = {
    "support": {"label": "General Support", "description": "Get help from our AI & support team", "emoji": "welcome"},
    "report": {"label": "Report", "description": "Report a member, bug, or staff issue", "emoji": "warning"},
    "giveaway": {"label": "Giveaway Claim", "description": "Claim a prize you won in a giveaway", "emoji": "promo"},
    "purchase": {"label": "Purchase", "description": "Buy members, perks, or server packages", "emoji": "ticket"},
}

TICKET_COMMANDS_CHANNEL_ID = 1556331435445461182
TICKET_TUTORIAL_CHANNEL_ID = 1556330642206359552
TICKET_VERIFY_CHANNEL_ID = 1556330642206359552

TICKET_AI_STATE = {}


def ticket_emoji(name):
    return discord.PartialEmoji.from_str(EMOJIS[name])


def ticket_owner_id(channel):
    match = re.search(r"owner:(\d+)", getattr(channel, "topic", None) or "")
    return int(match.group(1)) if match else None


def ticket_type_of(channel):
    match = re.search(r"type:(\w+)", getattr(channel, "topic", None) or "")
    return match.group(1) if match else "support"


def ticket_staff_requested(channel):
    state = TICKET_AI_STATE.get(channel.id)
    if state and state.get("staff_requested"):
        return True
    topic = getattr(channel, "topic", None) or ""
    return "staff_req:1" in topic


def get_ticket_staff_roles(guild):
    staff_roles = []
    supervisor_role_id = guild_setting("supervisor_roles", guild.id)
    if supervisor_role_id:
        sup_role = guild.get_role(int(supervisor_role_id))
        if sup_role:
            staff_roles.append(sup_role)
    for r in guild.roles:
        if r.is_default() or r.managed or r in staff_roles:
            continue
        lname = r.name.lower()
        if any(k in lname for k in ("staff team", "staff", "moderator", "trial mod", "admin", "support")):
            staff_roles.append(r)
    return staff_roles


async def escalate_ticket_to_staff(channel, triggered_by=None, reason_note="A human staff member has been requested."):
    guild = channel.guild
    state = TICKET_AI_STATE.setdefault(channel.id, {"staff_requested": False, "history": []})
    already_escalated = state.get("staff_requested", False) or ("staff_req:1" in (channel.topic or ""))
    state["staff_requested"] = True

    topic = channel.topic or ""
    if "staff_req:1" not in topic:
        try:
            await channel.edit(topic=f"{topic} | staff_req:1"[:1000])
        except discord.HTTPException:
            pass

    staff_roles = get_ticket_staff_roles(guild)
    for role in staff_roles:
        try:
            await channel.set_permissions(
                role,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
            )
        except discord.HTTPException:
            pass

    ping_mentions = " ".join(role.mention for role in staff_roles)
    if not ping_mentions and guild.owner:
        ping_mentions = guild.owner.mention

    if not already_escalated:
        embed = discord.Embed(
            title=f"{EMOJIS['shield']} Staff Assistance Requested",
            description=(
                f"{reason_note}\n\n"
                f"{EMOJIS['warning']} **Ticket AI Assistant has paused** so a human staff member can take over.\n"
                "Please wait patiently for a staff member to respond!"
            ),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text="MEMBERS RUSH • Ticket Escalation")
        await channel.send(
            content=ping_mentions or None,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=staff_roles, users=True),
        )
        await send_log(
            guild, "tickets", f"{EMOJIS['warning']} Staff Requested in Ticket",
            fields=[
                ("Ticket", channel.mention, True),
                ("Triggered by", triggered_by.mention if triggered_by else "Ticket AI / User", True),
                ("Reason", reason_note[:500], False),
            ],
            user=triggered_by,
        )
    return not already_escalated


def _detect_ticket_intent(content: str):
    text = (content or "").lower().strip()
    purchase_patterns = [
        r"\bpurchase\b", r"\bbuy\b", r"\bbuying\b", r"\border\b", r"\bmembers?\b",
        r"\bpay\b", r"\bpayment\b", r"\bprice\b", r"\bprices\b", r"\bpricing\b",
        r"\bpaypal\b", r"\bcrypto\b", r"\bltc\b", r"\bbtc\b", r"\busdt\b", r"\bcashapp\b", r"\bnitro\b",
    ]
    if any(re.search(p, text) for p in purchase_patterns):
        return "purchase"

    staff_patterns = [
        r"\bstaff\b", r"\bhuman\b", r"\breal person\b", r"\bmod\b", r"\bmoderator\b",
        r"\badmin\b", r"\bowner\b", r"\bsupervisor\b", r"\btalk to\b", r"\bspeak to\b",
        r"\bping staff\b", r"\bcall staff\b", r"\bneed a staff\b", r"\bhelp me staff\b",
        r"\bnot a bot\b", r"\bno ai\b",
    ]
    if any(re.search(p, text) for p in staff_patterns):
        return "staff"

    verify_patterns = [
        r"\bverif\w*\b", r"\bunverified\b", r"\bcaptcha\b", r"\bhow do i verify\b",
        r"\bcan'?t see channels\b", r"\baccess server\b",
    ]
    if any(re.search(p, text) for p in verify_patterns):
        return "verify"

    tutorial_patterns = [
        r"\btutorial\b", r"\bguide\b", r"\bhow to start\b", r"\bhow does this work\b",
        r"\bhow do i use\b", r"\bhow it works\b", r"\bgetting started\b", r"\bexplain\b",
    ]
    if any(re.search(p, text) for p in tutorial_patterns):
        return "tutorial"

    command_farm_patterns = [
        r"\bwhere\b.*\b(command|commands|cmd|cmds|farm|farming|grind|grinding|work|daily|bot)\b",
        r"\b(command|commands|cmd|cmds|farm|farming|grind|grinding)\b.*\bwhere\b",
        r"\bwhere do i\b", r"\bwhich channel\b", r"\bwhat channel\b",
        r"\buse commands\b", r"\bfarm channel\b", r"\bcommand channel\b", r"\bbot channel\b",
    ]
    if any(re.search(p, text) for p in command_farm_patterns):
        return "commands_farm"

    return None


async def handle_ticket_ai_message(message: discord.Message):
    channel = message.channel
    guild = message.guild
    if guild is None or ticket_owner_id(channel) is None:
        return
    if message.author.bot:
        return

    if ticket_staff_requested(channel):
        return

    if interaction_is_staff_member(message.author, guild):
        return

    intent = _detect_ticket_intent(message.content)

    if intent == "purchase":
        await escalate_ticket_to_staff(
            channel,
            triggered_by=message.author,
            reason_note="Wait for a staff member! A staff member has been pinged to assist with your purchase.",
        )
        return

    if intent == "staff":
        await escalate_ticket_to_staff(
            channel,
            triggered_by=message.author,
            reason_note="You asked to speak with staff. A staff member has been pinged and will be with you shortly!",
        )
        return

    if intent == "verify":
        embed = discord.Embed(
            title=f"{EMOJIS['shield']} How to Verify",
            description=(
                f"Head over to <#{TICKET_VERIFY_CHANNEL_ID}> and follow the instructions there to get verified!\n\n"
                f"If you still have trouble after checking <#{TICKET_VERIFY_CHANNEL_ID}>, click **Request Staff** below."
            ),
            color=discord.Color(0x2ECC71),
        )
        await message.reply(embed=embed, mention_author=False)
        return

    if intent == "tutorial":
        embed = discord.Embed(
            title=f"{EMOJIS['announcement']} Server & Bot Tutorial",
            description=(
                f"Check out our full step-by-step tutorial in <#{TICKET_TUTORIAL_CHANNEL_ID}>!\n\n"
                "If you need anything else or want a human staff member, click **Request Staff** below."
            ),
            color=discord.Color(0x2ECC71),
        )
        await message.reply(embed=embed, mention_author=False)
        return

    if intent == "commands_farm":
        embed = discord.Embed(
            title=f"{EMOJIS['gear']} Where to Use Commands & Farm",
            description=(
                f"Please use all bot commands and farming commands in <#{TICKET_COMMANDS_CHANNEL_ID}>!\n\n"
                "Need something else? Ask me here or click **Request Staff** below."
            ),
            color=discord.Color(0x2ECC71),
        )
        await message.reply(embed=embed, mention_author=False)
        return

    state = TICKET_AI_STATE.setdefault(channel.id, {"staff_requested": False, "history": []})
    history = state["history"][-10:]

    ticket_system_prompt = (
        f"You are the MEMBERS RUSH Ticket Support AI assisting {message.author.display_name} in a private support ticket in \"{guild.name}\". "
        "Important server routing rules you MUST follow accurately:\n"
        f"- If they ask where to use commands, farm, or grind, tell them to go to <#{TICKET_COMMANDS_CHANNEL_ID}>.\n"
        f"- If they ask for a tutorial or guide on how things work, direct them to <#{TICKET_TUTORIAL_CHANNEL_ID}>.\n"
        f"- If they ask how to verify or anything about verification, direct them to <#{TICKET_VERIFY_CHANNEL_ID}>.\n"
        "- If they want to purchase members or buy anything, tell them to wait for a staff member and include the exact tag [ESCALATE_PURCHASE] at the end of your reply.\n"
        "- If they ask to talk to a real human/staff member or you cannot solve their issue, include the exact tag [ESCALATE_STAFF] at the end of your reply.\n"
        "Be polite, concise, helpful, and never swear."
    )

    if not HF_API_KEY:
        fallback = discord.Embed(
            title=f"{EMOJIS['ticket']} Ticket AI Assistant",
            description=(
                f"• **Use Commands / Farm:** <#{TICKET_COMMANDS_CHANNEL_ID}>\n"
                f"• **Tutorial & Verification Guide:** <#{TICKET_TUTORIAL_CHANNEL_ID}>\n"
                "• **Need a Human Staff Member?** Click the **Request Staff** button above!"
            ),
            color=discord.Color(0x2ECC71),
        )
        await message.reply(embed=fallback, mention_author=False)
        return

    async with channel.typing():
        try:
            messages_payload = [{"role": "system", "content": ticket_system_prompt}] + history + [
                {"role": "user", "content": message.content[:1500]}
            ]
            raw_reply = await _ai_post(messages_payload, max_tokens=500, temperature=0.4)
            raw_reply = re.sub(r"<think>.*?</think>", "", raw_reply, flags=re.DOTALL).strip()

            if "[ESCALATE_PURCHASE]" in raw_reply:
                await escalate_ticket_to_staff(
                    channel,
                    triggered_by=message.author,
                    reason_note="Wait for a staff member! A staff member has been pinged to assist with your purchase.",
                )
                return

            if "[ESCALATE_STAFF]" in raw_reply:
                await escalate_ticket_to_staff(
                    channel,
                    triggered_by=message.author,
                    reason_note="A staff member has been pinged to assist you!",
                )
                return

            placeholder_cmd = "__CMD_CH_LINK__"
            placeholder_tut = "__TUT_CH_LINK__"
            cleaned = raw_reply.replace(f"<#{TICKET_COMMANDS_CHANNEL_ID}>", placeholder_cmd).replace(f"<#{TICKET_TUTORIAL_CHANNEL_ID}>", placeholder_tut)
            cleaned = sanitize_ai_output(cleaned)
            cleaned = cleaned.replace(placeholder_cmd, f"<#{TICKET_COMMANDS_CHANNEL_ID}>").replace(placeholder_tut, f"<#{TICKET_TUTORIAL_CHANNEL_ID}>")

            state["history"] = (history + [
                {"role": "user", "content": message.content[:1000]},
                {"role": "assistant", "content": cleaned[:1000]},
            ])[-10:]

            await message.reply(cleaned[:1900], mention_author=False, allowed_mentions=discord.AllowedMentions.none())
        except Exception:
            logging.exception("Ticket AI error")
            await message.reply(
                f"I'm having a quick hiccup! You can click **Request Staff** above if you'd like a staff member right away.",
                mention_author=False,
            )


def interaction_is_staff_member(member, guild):
    if guild is None or not isinstance(member, discord.Member):
        return False
    extra_ids = {str(uid) for uid in config.get("extra_owners", {}).get(str(guild.id), [])}
    if member.id == OWNER_ID or member.id == guild.owner_id or str(member.id) in extra_ids:
        return True
    role_id = guild_setting("supervisor_roles", guild.id)
    if role_id and any(role.id == int(role_id) for role in member.roles):
        return True
    if member.guild_permissions.kick_members or member.guild_permissions.administrator:
        return True
    return any(k in r.name.lower() for r in member.roles for k in ("staff", "trial", "mod", "supervisor", "admin"))


def interaction_is_staff(interaction):
    return interaction_is_staff_member(interaction.user, interaction.guild)


async def build_ticket_transcript(channel, closed_by):
    lines = [
        f"Transcript of #{channel.name} ({channel.id})",
        f"Closed by {closed_by} ({closed_by.id}) at {discord.utils.utcnow():%Y-%m-%d %H:%M UTC}",
        "-" * 60,
    ]
    count = 0
    async for message in channel.history(limit=2000, oldest_first=True):
        stamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        text = message.clean_content or ""
        for embed in message.embeds:
            text += f" [embed: {embed.title or ''} {embed.description or ''}]"
        attachments = " ".join(a.url for a in message.attachments)
        lines.append(f"[{stamp}] {message.author} ({message.author.id}): {text} {attachments}".rstrip())
        count += 1
    return "\n".join(lines).encode("utf-8"), count


async def close_ticket_channel(channel, closer, reason):
    guild = channel.guild
    owner_id = ticket_owner_id(channel)
    ticket_type = TICKET_TYPES.get(ticket_type_of(channel), TICKET_TYPES["support"])["label"]
    TICKET_AI_STATE.pop(channel.id, None)
    try:
        data, count = await build_ticket_transcript(channel, closer)
    except discord.HTTPException:
        data, count = b"Transcript unavailable.", 0
    file_name = f"{channel.name}.txt"
    await send_log(
        guild, "tickets", f"{EMOJIS['error']} Ticket Closed",
        fields=[
            ("Ticket", f"#{channel.name}", True),
            ("Category", ticket_type, True),
            ("Opened by", f"<@{owner_id}>" if owner_id else "Unknown", True),
            ("Closed by", closer.mention, True),
            ("Messages", count, True),
            ("Reason", reason or "No reason provided", False),
        ],
        user=closer,
        file=discord.File(io.BytesIO(data), filename=file_name),
    )
    owner = guild.get_member(owner_id) if owner_id else None
    if owner is not None:
        dm_embed = discord.Embed(
            title=f"{EMOJIS['ticket']} Your ticket was closed",
            description=f"Your **{ticket_type}** ticket in **{guild.name}** was closed.\n**Reason:** {reason or 'No reason provided'}",
            color=discord.Color(0x2ECC71),
            timestamp=discord.utils.utcnow(),
        )
        try:
            await owner.send(embed=dm_embed, file=discord.File(io.BytesIO(data), filename=file_name))
        except discord.HTTPException:
            pass
    await asyncio.sleep(5)
    try:
        await channel.delete(reason=f"Ticket closed by {closer}: {reason}"[:480])
    except discord.HTTPException:
        pass


class TicketCloseModal(discord.ui.Modal, title="Close Ticket"):
    reason = discord.ui.TextInput(label="Reason (optional)", style=discord.TextStyle.paragraph, required=False, max_length=300, placeholder="Why is this ticket being closed?")

    async def on_submit(self, interaction: discord.Interaction):
        reason = str(self.reason.value or "").strip() or "No reason provided"
        await interaction.response.send_message(embed=discord.Embed(
            description=f"{EMOJIS['warning']} Closing this ticket in 5 seconds...\n**Reason:** {reason}",
            color=discord.Color(0x2ECC71),
        ))
        await close_ticket_channel(interaction.channel, interaction.user, reason)


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.request_staff.emoji = ticket_emoji("shield")
        self.claim_ticket.emoji = ticket_emoji("success")
        self.close_ticket.emoji = ticket_emoji("error")

    @discord.ui.button(label="Request Staff", style=discord.ButtonStyle.blurple, custom_id="ticket_request_staff_btn")
    async def request_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        if ticket_staff_requested(channel):
            await interaction.response.send_message(
                f"{EMOJIS['warning']} Staff have already been requested and unlocked in this ticket! Please wait for them to reply.",
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True)
        await escalate_ticket_to_staff(
            channel,
            triggered_by=interaction.user,
            reason_note=f"{interaction.user.mention} clicked **Request Staff** and is waiting for a staff member!",
        )
        await interaction.followup.send(f"{EMOJIS['success']} Staff have been pinged and unlocked in this ticket!", ephemeral=True)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, custom_id="ticket_claim_btn")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction_is_staff(interaction):
            await interaction.response.send_message(f"{EMOJIS['error']} Only staff can claim tickets.", ephemeral=True)
            return
        channel = interaction.channel
        topic = channel.topic or ""
        claimed = re.search(r"claimed:(\d+)", topic)
        if claimed:
            await interaction.response.send_message(f"{EMOJIS['warning']} Already claimed by <@{claimed.group(1)}>.", ephemeral=True)
            return
        state = TICKET_AI_STATE.setdefault(channel.id, {"staff_requested": True, "history": []})
        state["staff_requested"] = True
        for role in get_ticket_staff_roles(interaction.guild):
            try:
                await channel.set_permissions(role, view_channel=True, send_messages=True, read_message_history=True, attach_files=True)
            except discord.HTTPException:
                pass
        await interaction.response.send_message(embed=discord.Embed(
            description=f"{EMOJIS['success']} {interaction.user.mention} has claimed this ticket.",
            color=discord.Color(0x2ECC71),
        ))
        try:
            await channel.edit(topic=f"{topic} | claimed:{interaction.user.id} | staff_req:1"[:1000])
        except discord.HTTPException:
            pass
        await send_log(interaction.guild, "tickets", f"{EMOJIS['success']} Ticket Claimed", fields=[("Ticket", channel.mention, True), ("Claimed by", interaction.user.mention, True)], user=interaction.user)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        owner_id = ticket_owner_id(interaction.channel)
        if not (interaction_is_staff(interaction) or interaction.user.id == owner_id):
            await interaction.response.send_message(f"{EMOJIS['error']} Only staff or the ticket owner can close this ticket.", ephemeral=True)
            return
        await interaction.response.send_modal(TicketCloseModal())


class TicketSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.create_ticket.options = [
            discord.SelectOption(label=info["label"], value=key, description=info["description"], emoji=ticket_emoji(info["emoji"]))
            for key, info in TICKET_TYPES.items()
        ]

    @discord.ui.select(placeholder="Choose a ticket type...", min_values=1, max_values=1, custom_id="ticket_type_select", options=[discord.SelectOption(label="General Support", value="support")])
    async def create_ticket(self, interaction: discord.Interaction, select: discord.ui.Select):
        guild = interaction.guild
        member = interaction.user
        ticket_type = select.values[0] if select.values[0] in TICKET_TYPES else "support"
        info = TICKET_TYPES[ticket_type]

        for existing in guild.text_channels:
            if ticket_owner_id(existing) == member.id and ticket_type_of(existing) == ticket_type:
                await interaction.response.send_message(f"{EMOJIS['error']} You already have this ticket open: {existing.mention}", ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_permissions=True, read_message_history=True),
        }
        staff_roles = get_ticket_staff_roles(guild)
        for role in staff_roles:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=False,
                read_message_history=True,
                attach_files=False,
            )

        category = discord.utils.get(guild.categories, name="Support Tickets")
        try:
            if not category:
                category = await guild.create_category("Support Tickets")
            slug = re.sub(r"[^a-z0-9]", "", member.name.lower())[:20] or str(member.id)
            channel = await guild.create_text_channel(
                name=f"ticket-{ticket_type}-{slug}",
                category=category,
                overwrites=overwrites,
                topic=f"{info['label']} ticket for {member} | owner:{member.id} | type:{ticket_type}",
            )
        except discord.HTTPException:
            await interaction.followup.send(f"{EMOJIS['error']} I couldn't create your ticket. I need the Manage Channels permission.", ephemeral=True)
            return

        TICKET_AI_STATE[channel.id] = {"staff_requested": False, "history": []}

        embed = discord.Embed(
            title=f"{EMOJIS['announcement']} {info['label']} Ticket",
            description=(
                f"Hello {member.mention}! Our **MEMBERS RUSH AI Assistant** is here to help you right away.\n\n"
                f"{EMOJIS['bullet']} **Ask your question below** — the AI will guide you instantly!\n"
                f"{EMOJIS['bullet']} Need a human staff member? Click **Request Staff** below or ask to speak with staff."
            ),
            color=discord.Color(0x2ECC71),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Opened by", value=member.mention, inline=True)
        embed.add_field(name="Category", value=info["label"], inline=True)
        embed.set_footer(text="MEMBERS RUSH • AI Ticket Support")
        apply_embed_theme(guild.id, embed)

        await channel.send(
            content=member.mention,
            embed=embed,
            view=TicketControlView(),
            allowed_mentions=discord.AllowedMentions(users=[member]),
        )
        await interaction.followup.send(f"{EMOJIS['success']} Your {info['label']} ticket is ready: {channel.mention}", ephemeral=True)
        await send_log(
            guild, "tickets", f"{EMOJIS['announcement']} Ticket Opened",
            fields=[("Ticket", channel.mention, True), ("Category", info["label"], True), ("Opened by", member.mention, True)],
            user=member,
        )

        if ticket_type == "purchase":
            await escalate_ticket_to_staff(
                channel,
                triggered_by=member,
                reason_note="Wait for a staff member! You opened a **Purchase** ticket, so a staff member has been pinged to assist you.",
            )


async def ticket_command_guard(ctx, allow_owner=False):
    owner_id = ticket_owner_id(ctx.channel)
    if owner_id is None:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} This command only works inside a ticket channel.", color=discord.Color.red()), ephemeral=True)
        return False
    if user_is_staff(ctx) or (allow_owner and ctx.author.id == owner_id):
        return True
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()), ephemeral=True)
    return False


@bot.hybrid_group(name="ticket", invoke_without_command=True)
@commands.guild_only()
async def ticket_group(ctx):
    """Manage the ticket you are in."""
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['ticket']} Use `/ticket add`, `/ticket remove` or `/ticket close` inside a ticket channel.", color=discord.Color(0x2ECC71)))


@ticket_group.command(name="add")
@commands.guild_only()
async def ticket_add(ctx, member: discord.Member):
    """Add a member to this ticket."""
    if not await ticket_command_guard(ctx):
        return
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Added {member.mention} to this ticket.", color=discord.Color(0x2ECC71)))
    await send_log(ctx.guild, "tickets", f"{EMOJIS['success']} Ticket Member Added", fields=[("Ticket", ctx.channel.mention, True), ("Added", member.mention, True), ("By", ctx.author.mention, True)], user=ctx.author)


@ticket_group.command(name="remove")
@commands.guild_only()
async def ticket_remove(ctx, member: discord.Member):
    """Remove a member from this ticket."""
    if not await ticket_command_guard(ctx):
        return
    if member.id == ticket_owner_id(ctx.channel):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} You can't remove the ticket owner. Close the ticket instead.", color=discord.Color.orange()))
        return
    await ctx.channel.set_permissions(member, overwrite=None)
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Removed {member.mention} from this ticket.", color=discord.Color(0x2ECC71)))
    await send_log(ctx.guild, "tickets", f"{EMOJIS['warning']} Ticket Member Removed", fields=[("Ticket", ctx.channel.mention, True), ("Removed", member.mention, True), ("By", ctx.author.mention, True)], user=ctx.author)


@ticket_group.command(name="close")
@commands.guild_only()
async def ticket_close(ctx, *, reason: str = "No reason provided"):
    """Close this ticket and save a transcript."""
    if not await ticket_command_guard(ctx, allow_owner=True):
        return
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Closing this ticket in 5 seconds...\n**Reason:** {reason}", color=discord.Color(0x2ECC71)))
    await close_ticket_channel(ctx.channel, ctx.author, reason)


# =========================
# EMBED HELPERS
# =========================

async def send_promodemo_embed(guild, member, role, action, moderator, reason="No reason provided"):
    setting_key = "promo_channels" if action == "promoted" else "demo_channels"
    channel_id = guild_setting(setting_key, guild.id) or guild_setting("promodemo_channels", guild.id)
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
    embed.add_field(name=f"{EMOJIS['warning']} Reason", value=reason[:1024], inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"{guild.name} • MEMBERS RUSH System")
    apply_embed_theme(guild.id, embed)

    try:
        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        pass


async def change_staff_role(ctx, member, target_role, action, reason="No reason provided"):
    if target_role is None:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} The specified or configured role could not be found in this server.", color=discord.Color.red()))
        return

    if member.id == ctx.author.id or member.id == ctx.guild.owner_id or target_role.is_default() or target_role.managed:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Action unauthorized or invalid role.", color=discord.Color.orange()))
        return

    try:
        if action == "promote":
            await member.add_roles(target_role, reason=f"{reason} (Staff promotion by {ctx.author})"[:480])
            result = "promoted"
        else:
            await member.remove_roles(target_role, reason=f"{reason} (Staff demotion by {ctx.author})"[:480])
            result = "demoted"

        await send_promodemo_embed(ctx.guild, member, target_role, result, ctx.author, reason)
        await audit(ctx.guild, f"Staff {result}: {member} | Role: {target_role.name} | Reason: {reason} | By: {ctx.author}")
        emoji = EMOJIS['promo'] if result == "promoted" else EMOJIS['demo']
        await ctx.reply(embed=discord.Embed(description=f"{emoji} {member.mention} was **{result}**: {target_role.mention}\n**Reason:** {reason}", color=discord.Color.green() if result == "promoted" else discord.Color.red()))
    except discord.Forbidden:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Missing permissions to modify roles.", color=discord.Color.red()))


# =========================
# MANAGEMENT & STAFF COMMANDS (Converted to standard prefix commands to avoid CommandLimitReached)
# =========================

@bot.command(name="promo")
@commands.guild_only()
async def promo_prefix(ctx, staff: discord.Member, target_role: discord.Role = None, *, reason: str = "No reason provided"):
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

    await change_staff_role(ctx, staff, target_role, "promote", reason)


@bot.command(name="demo")
@commands.guild_only()
async def demo_prefix(ctx, staff: discord.Member, target_role: discord.Role = None, *, reason: str = "No reason provided"):
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

    await change_staff_role(ctx, staff, target_role, "demote", reason)


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
    """Show the supervisor command guide."""
    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass

    if not user_is_supervisor(ctx):
        err_msg = await ctx.send(embed=discord.Embed(description=f"{EMOJIS['error']} Only staff supervisors can use this command.", color=discord.Color.red()))
        try:
            await err_msg.delete(delay=5)
        except discord.HTTPException:
            pass
        return

    embed = discord.Embed(
        title=f"{EMOJIS['welcome']} Welcome Staff Supervisor!",
        description=(
            f"Welcome to the **MEMBERS RUSH Supervisor System**! {EMOJIS['shield']}\n"
            "As a Supervisor, you have permission to manage the staff hierarchy using automated rank ladder commands."
        ),
        color=discord.Color(0x2ECC71),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name=f"{EMOJIS['promo']} `>promo @member [@role] [reason]`",
        value=(
            f"{EMOJIS['bullet']} Promotes a staff member.\n"
            f"{EMOJIS['bullet']} **Auto Ladder:** If no role is given, advances them to the next step up."
        ),
        inline=False
    )

    embed.add_field(
        name=f"{EMOJIS['demo']} `>demo @member [@role] [reason]`",
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

    embed.set_footer(text=f"Requested by {ctx.author.display_name} • MEMBERS RUSH Guide", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name="staffintro")
@commands.guild_only()
async def staffintro(ctx):
    """Show the staff moderation command guide."""
    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass

    if not user_is_staff(ctx):
        err_msg = await ctx.send(embed=discord.Embed(description=f"{EMOJIS['error']} Only staff members can use this command.", color=discord.Color.red()))
        try:
            await err_msg.delete(delay=5)
        except discord.HTTPException:
            pass
        return

    embed = discord.Embed(
        title=f"{EMOJIS['welcome']} Welcome to the MEMBERS RUSH Staff Team!",
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
        name=f"{EMOJIS['ladder']} Staff Activity",
        value=f"{EMOJIS['bullet']} `>sl` — Shows staff invite, message, and moderation totals.\n"
              f"{EMOJIS['bullet']} `>bam @member [reason]` — Posts a clearly labelled fake-ban joke; it does not ban anyone.",
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

    embed.set_footer(text=f"Requested by {ctx.author.display_name} • MEMBERS RUSH Guide", icon_url=ctx.author.display_avatar.url)
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
        suppress_log(ctx.guild.id, member.id, "kick")
        await member.kick(reason=f"{reason} (Kicked by {ctx.author})")
        add_staff_stat(ctx.guild.id, ctx.author.id, "moderation")
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
        suppress_log(ctx.guild.id, member.id, "ban")
        await member.ban(reason=f"{reason} (Banned by {ctx.author})")
        add_staff_stat(ctx.guild.id, ctx.author.id, "moderation")
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Banned {member.mention} | Reason: {reason}", color=discord.Color.red()))
        await audit(ctx.guild, f"Member banned: {member} ({member.id}) | Reason: {reason} | By: {ctx.author}")
    except discord.Forbidden:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} I lack permissions to ban that member.", color=discord.Color.red()))


@bot.command(name="bam", aliases=["fakeban"])
@commands.guild_only()
async def fake_ban(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    """Post a labelled fake-ban gag; it never bans or restricts anyone."""
    if not user_is_staff(ctx):
        return await ctx.reply(embed=discord.Embed(
            description=f"{EMOJIS['error']} You don't have permission to use this command.",
            color=discord.Color.red()))
    embed = discord.Embed(
        title=f"{EMOJIS['warning']} SIMULATED BAN",
        description=(f"{member.mention} has been **pretend-banned**.\n\n"
                     f"**Reason:** {reason[:900]}\n\n"
                     "**Joke announcement only: no ban was issued and access is unchanged.**"),
        color=discord.Color.orange(), timestamp=discord.utils.utcnow())
    embed.set_footer(text="MEMBERS RUSH • Fake ban / no moderation action")
    await ctx.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())


@bot.command(name="clear")
@commands.guild_only()
async def clear(ctx, amount: commands.Range[int, 1, 100] = 5):
    """Delete recent messages in this channel (1-100)."""
    if not user_is_staff(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()), ephemeral=True)
        return

    if ctx.interaction is not None:
        await ctx.defer(ephemeral=True)
        deleted = await ctx.channel.purge(limit=amount)
        add_staff_stat(ctx.guild.id, ctx.author.id, "moderation")
        await ctx.send(embed=discord.Embed(description=f"{EMOJIS['success']} Cleared {len(deleted)} messages.", color=discord.Color(0x2ECC71)), ephemeral=True)
    else:
        await ctx.channel.purge(limit=amount + 1)
        add_staff_stat(ctx.guild.id, ctx.author.id, "moderation")
        msg = await ctx.send(embed=discord.Embed(description=f"{EMOJIS['success']} Cleared {amount} messages.", color=discord.Color(0x2ECC71)))
        await msg.delete(delay=3)
    await audit(ctx.guild, f"Messages cleared: {amount} in {ctx.channel.mention} | By: {ctx.author}")


@bot.command(name="mute")
@commands.guild_only()
async def mute(ctx, member: discord.Member, *, reason="No reason provided"):
    """Timeouts a member."""
    if not user_is_staff(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    from datetime import timedelta
    try:
        suppress_log(ctx.guild.id, member.id, "timeout")
        await member.timeout(timedelta(minutes=10), reason=f"{reason} (Muted by {ctx.author




