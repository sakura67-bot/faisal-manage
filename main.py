import os
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
from discord.ext import commands
from aiohttp import web

# =========================
# CONFIGURATION
# =========================

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))
PORT = int(os.getenv("SERVER_PORT", os.getenv("PORT", 8080)))
ECONOMY_CHANNEL_ID = 1567948104756371597
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
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Supreme Bot Dashboard</title>
<style>:root{color-scheme:dark;--bg:#080b16;--card:#11182a;--line:#293653;--accent:#a58bff;--accent2:#65e2d1;--text:#f6f5ff;--muted:#aab5ce;--shadow:0 24px 70px #0008}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:radial-gradient(ellipse at 10% -10%,#48358b88,transparent 35%),radial-gradient(ellipse at 100% 20%,#146b7770,transparent 30%),var(--bg);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--text);min-height:100vh}body:before{content:'';position:fixed;inset:0;pointer-events:none;opacity:.16;background-image:radial-gradient(#c7bdff .6px,transparent .6px);background-size:24px 24px;mask-image:linear-gradient(to bottom,#000,transparent 80%)}.wrap{position:relative;max-width:1120px;margin:0 auto;padding:32px 22px 60px}.bar{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;padding:14px 18px;background:#0e1425b8;border:1px solid #a99cff27;border-radius:18px;backdrop-filter:blur(16px);box-shadow:0 12px 36px #0003}.tag{color:#d0c6ff;font-weight:800;letter-spacing:.14em;text-transform:uppercase;font-size:11px}.bar .small{margin-top:3px}.hero{position:relative;overflow:hidden;margin:24px 0 20px;padding:36px 34px;border:1px solid #baaaff33;border-radius:26px;background:linear-gradient(120deg,#271d4ddd,#11182bdd 65%,#12353ddd);box-shadow:var(--shadow)}.hero:after{content:'✦';position:absolute;right:7%;top:-65px;font-size:230px;line-height:1;color:#d8d0ff0b;transform:rotate(12deg);pointer-events:none}.hero h1{max-width:720px;font-size:clamp(34px,6vw,58px);line-height:1.05;letter-spacing:-.045em;margin:11px 0 14px}.hero p{max-width:700px;margin:0;color:#c3c8df;font-size:16px}.hero:before{content:'CONTROL CENTER  /  YOUR SERVER';display:inline-flex;color:#aaf7e8;font-size:10px;font-weight:800;letter-spacing:.16em}.card{position:relative;background:linear-gradient(145deg,#151e32f2,#101626f5);border:1px solid #c5caff1c;border-radius:20px;padding:24px;margin:18px 0;box-shadow:0 18px 50px #02040b75;transition:transform .22s,border-color .22s,box-shadow .22s}.card:hover{border-color:#a58bff50;box-shadow:0 22px 60px #02040b99,0 0 28px #8e70ff0d}.card h2{display:flex;align-items:center;gap:10px;margin:0 0 4px;font-size:21px;letter-spacing:-.02em}.card h2:before{content:'';width:4px;height:22px;border-radius:5px;background:linear-gradient(var(--accent),var(--accent2));box-shadow:0 0 14px #a58bff88}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px;margin-top:16px}.field{display:flex;flex-direction:column;gap:8px;margin:9px 0}label{font-size:13px;font-weight:700;color:#e3e3f5}input,select,textarea{background:#0b1120;color:var(--text);border:1px solid #35415e;border-radius:12px;padding:12px 14px;font:inherit;width:100%;outline:0;transition:border-color .18s,box-shadow .18s,background .18s}input:focus,select:focus,textarea:focus{border-color:#a58bff;box-shadow:0 0 0 3px #a58bff24;background:#10172a}input[type=color]{height:47px;padding:5px;cursor:pointer}textarea{min-height:115px;resize:vertical}button,.button{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:linear-gradient(120deg,#b09aff,#8b72ef);color:#151026;border:1px solid #d9cdff55;border-radius:12px;padding:12px 18px;font:inherit;font-weight:800;text-decoration:none;cursor:pointer;margin:7px 8px 0 0;box-shadow:0 8px 24px #8d70e933;transition:transform .18s,filter .18s,box-shadow .18s}button:hover,.button:hover{transform:translateY(-2px);filter:brightness(1.08);box-shadow:0 12px 30px #8d70e955}button:active,.button:active{transform:translateY(0)}button.secondary{background:#202b43;color:#e7eaff;border-color:#6a789555;box-shadow:none}.small{font-size:12px;color:var(--muted)}.hidden{display:none}.row{display:flex;gap:10px;align-items:center}.status{min-height:26px;color:#a7f4d5;margin-top:12px}.preview{white-space:pre-wrap;background:linear-gradient(110deg,#0b1120,#11192a);border:1px solid #293653;border-left:4px solid var(--accent);padding:16px;border-radius:12px;min-height:76px;color:#e2e5f5;margin-top:12px}.card>p{color:var(--muted);line-height:1.65;margin:4px 0 10px}.card .field .small{line-height:1.5}@media(max-width:700px){.grid{grid-template-columns:1fr}.wrap{padding:16px 12px 38px}.card{padding:18px;border-radius:16px}.hero{padding:28px 22px;border-radius:20px}.hero:after{right:-8%;top:-25px;font-size:150px}.bar{padding:12px 14px}}.shop-items{display:grid;gap:10px;margin-top:20px}.shop-item{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:14px 16px;background:#0b1120;border:1px solid #293653;border-radius:13px}.shop-item strong{color:#fff}.shop-item .small{margin-top:3px}.shop-item button{padding:8px 12px}.shop-price{color:#aaf7e8;font-weight:800;white-space:nowrap}@media(max-width:700px){.shop-item{align-items:flex-start;flex-direction:column}}.dash-nav{position:sticky;top:10px;z-index:5;display:flex;gap:8px;flex-wrap:wrap;padding:10px;margin:14px 0 20px;background:#0c1220dd;border:1px solid #b8adff24;border-radius:16px;backdrop-filter:blur(16px)}.dash-nav a{color:#d9d9ee;text-decoration:none;font-size:13px;font-weight:750;padding:9px 13px;border-radius:10px;transition:.18s}.dash-nav a:hover{color:#fff;background:#a58bff29}.card[id]{scroll-margin-top:90px}</style></head><body><main class="wrap"><div class="bar"><div><div class="tag">Supreme Bot • Bot-Hosting.net</div><div class="small">Server dashboard</div></div><button class="secondary" onclick="logout()">Log out</button></div>
<section class="hero"><h1>Bot control panel</h1><p>One beautiful control center for your server setup, embeds, tickets, wallets, and a fully editable member shop. Dashboard access is limited to the bot owner and trusted extra owners.</p></section>
<nav class="dash-nav" aria-label="Dashboard sections"><a href="#settings">⚙️ Server</a><a href="#moneyCard">💰 Economy</a><a href="#embedCard">✦ Embeds</a><a href="#shopCard">🛍️ Shop</a></nav>
<section class="card"><div class="field"><label for="guild">Discord server</label><select id="guild"></select></div><div id="settings" class="hidden"><h2>Server settings</h2><p class="small">Prefix, staff destinations, embed appearance, and ticket panel content are saved per server.</p><div class="grid">
<div class="field"><label for="prefix">Command prefix</label><input id="prefix" maxlength="5" value=">"><span class="small">Example: `>` or `!`</span></div>
<div class="field"><label for="supervisor">Supervisor role</label><select id="supervisor"></select></div>
<div class="field"><label for="promodemo">Promotion / demotion channel</label><select id="promodemo"></select></div><div class="field"><label for="audit">Audit log channel</label><select id="audit"></select></div>
<div class="field"><label for="embedColor">Default embed color</label><input id="embedColor" type="color" value="#5865f2"></div><div class="field"><label for="footer">Default embed footer</label><input id="footer" maxlength="200" placeholder="Supreme Bot"></div>
<div class="field"><label for="ticketTitle">Ticket panel title</label><input id="ticketTitle" maxlength="100"></div><div class="field"><label for="ticketChannel">Ticket panel channel</label><select id="ticketChannel"></select></div>
<div class="field"><label for="ticketDescription">Ticket panel description</label><textarea id="ticketDescription" maxlength="2000"></textarea></div>
<div class="field"><label for="dailyMin">Daily reward minimum</label><input id="dailyMin" type="number" min="0" max="1000000"></div><div class="field"><label for="dailyMax">Daily reward maximum</label><input id="dailyMax" type="number" min="0" max="1000000"></div><div class="field"><label for="workMin">Work reward minimum</label><input id="workMin" type="number" min="0" max="1000000"></div><div class="field"><label for="workMax">Work reward maximum</label><input id="workMax" type="number" min="0" max="1000000"></div><div class="field"><label for="workCooldown">Work cooldown (seconds)</label><input id="workCooldown" type="number" min="10" max="86400"></div>
</div><button onclick="saveSettings()">Save server settings</button><button class="secondary" onclick="postPanel()">Post ticket dropdown</button><div id="settingsStatus" class="status"></div></div><div id="empty" class="small hidden">No eligible servers found. Ask the bot owner to add you with >addextraowner if you need dashboard access.</div></section>
<section id="moneyCard" class="card hidden"><h2>Economy manager</h2><p class="small">Change a member’s coins. Your Discord account needs server management access.</p><div class="grid"><div class="field"><label for="moneyUser">Member ID</label><input id="moneyUser" inputmode="numeric" placeholder="Discord user ID"></div><div class="field"><label for="moneyAction">Action</label><select id="moneyAction"><option value="add">Add coins</option><option value="remove">Remove coins</option><option value="set">Set balance</option><option value="reset">Reset wallet</option></select></div><div class="field"><label for="moneyAmount">Amount</label><input id="moneyAmount" type="number" min="0" max="1000000000" value="100"></div></div><button onclick="manageMoney()">Apply economy change</button><div id="moneyStatus" class="status"></div></section><section id="embedCard" class="card hidden"><h2>Embed builder</h2><p class="small">Create and send a custom embed to a channel. Field rows use `name | value | inline`; use `true` or `false` for inline.</p><div class="grid"><div class="field"><label for="embedChannel">Post in</label><select id="embedChannel"></select></div><div class="field"><label for="customColor">Embed color</label><input id="customColor" type="color" value="#5865f2"></div><div class="field"><label for="customTitle">Title</label><input id="customTitle" maxlength="256" placeholder="Announcement"></div><div class="field"><label for="customFooter">Footer</label><input id="customFooter" maxlength="200" placeholder="Optional footer"></div>
<div class="field"><label for="customAuthor">Author label</label><input id="customAuthor" maxlength="256" placeholder="Optional author"></div><div class="field"><label for="customUrl">Title link (HTTPS URL)</label><input id="customUrl" maxlength="2048" placeholder="https://example.com"></div><div class="field"><label for="customImage">Image URL (HTTPS)</label><input id="customImage" maxlength="2048" placeholder="https://example.com/image.png"></div><div class="field"><label for="customThumb">Thumbnail URL (HTTPS)</label><input id="customThumb" maxlength="2048" placeholder="https://example.com/thumb.png"></div><div class="field"><label for="customDescription">Description</label><textarea id="customDescription" maxlength="4000" placeholder="Write your embed message"></textarea></div><div class="field"><label for="customFields">Fields (one per line)</label><textarea id="customFields" placeholder="Rules | Be kind to everyone | false&#10;Need help? | Open a ticket below | true"></textarea></div></div><div class="preview" id="preview">Embed preview will appear here.</div><button onclick="sendEmbed()">Send embed</button><div id="embedStatus" class="status"></div></section>
<section id="shopCard" class="card hidden"><h2>Shop studio</h2><p class="small">Create and edit the items members can buy. Each item has its own emoji, name, description, and coin price.</p><div class="grid"><div class="field"><label for="shopId">Item ID</label><input id="shopId" maxlength="24" placeholder="golden_crown"></div><div class="field"><label for="shopName">Item name</label><input id="shopName" maxlength="80" placeholder="Golden Crown"></div><div class="field"><label for="shopPrice">Price</label><input id="shopPrice" type="number" min="1" max="1000000000" placeholder="500"></div><div class="field"><label for="shopEmoji">Emoji</label><input id="shopEmoji" maxlength="80" placeholder="👑 or <:crown:123...>"></div><div class="field"><label for="shopDescription">Description</label><input id="shopDescription" maxlength="200" placeholder="A shiny crown for your collection"></div></div><button onclick="saveShopItem()">Save shop item</button><button class="secondary" onclick="clearShopForm()">New item</button><div id="shopStatus" class="status"></div><div id="shopItems" class="shop-items"></div></section><section id="activityCard" class="card hidden"><h2>Bot activity</h2><p class="small">This changes the bot-wide Discord presence. Only the bot owner can save it.</p><div class="grid"><div class="field"><label for="activityType">Activity</label><select id="activityType"><option>playing</option><option>streaming</option><option>listening</option><option>watching</option><option>competing</option></select></div><div class="field"><label for="activityText">Activity text</label><input id="activityText" maxlength="128" placeholder="Supreme Bot"></div></div><button class="secondary" onclick="saveActivity()">Save activity</button><div id="activityStatus" class="status"></div></section>
<p class="small">The website runs inside this bot deployment. Activate a Bot-Hosting.net HTTPS subdomain and set the Discord OAuth redirect URL to `/oauth/callback`.</p></main>
<script>
const guildSelect=document.getElementById('guild'),settings=document.getElementById('settings'),statusBox=document.getElementById('settingsStatus');
async function api(path,options={}){const response=await fetch(path,{credentials:'same-origin',headers:{'Content-Type':'application/json',...(options.headers||{})},...options});if(response.status===401){location.href='/login';throw new Error('Please sign in again.')}const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');return data}
function fill(id,items,selected,label){const el=document.getElementById(id);el.replaceChildren(new Option(label,''));for(const item of items)el.add(new Option(item.name,item.id));if(selected)el.value=String(selected)}
async function loadGuilds(){try{const data=await api('/api/guilds');if(!data.guilds.length){document.getElementById('empty').classList.remove('hidden');return}for(const g of data.guilds)guildSelect.add(new Option(g.name+" · "+g.id,g.id));await loadConfig()}catch(e){statusBox.textContent=e.message}}
async function loadConfig(){try{const d=await api('/api/guild/'+guildSelect.value);fill('supervisor',d.roles,d.supervisor_role,'No supervisor role');fill('promodemo',d.channels,d.promodemo_channel,'Not set');fill('audit',d.channels,d.audit_channel,'Not set');fill('ticketChannel',d.channels,null,'Choose a channel');fill('embedChannel',d.channels,null,'Choose a channel');document.getElementById('prefix').value=d.prefix;document.getElementById('embedColor').value=d.embed_color;document.getElementById('footer').value=d.embed_footer;document.getElementById('ticketTitle').value=d.ticket_title;document.getElementById('ticketDescription').value=d.ticket_description;document.getElementById('dailyMin').value=d.economy.daily_min;document.getElementById('dailyMax').value=d.economy.daily_max;document.getElementById('workMin').value=d.economy.work_min;document.getElementById('workMax').value=d.economy.work_max;document.getElementById('workCooldown').value=d.economy.work_cooldown;document.getElementById('activityType').value=d.activity_type||'playing';document.getElementById('activityText').value=d.activity_text||'';document.getElementById('activityCard').classList.toggle('hidden',!d.can_set_activity);settings.classList.remove('hidden');document.getElementById('moneyCard').classList.remove('hidden');document.getElementById('embedCard').classList.remove('hidden');document.getElementById('shopCard').classList.remove('hidden');renderShopItems(d.shop_items||[]);document.getElementById('empty').classList.add('hidden')}catch(e){statusBox.textContent=e.message}}
guildSelect.addEventListener('change',loadConfig);
async function saveSettings(){statusBox.textContent='Saving…';try{await api('/api/guild/'+guildSelect.value+'/settings',{method:'POST',body:JSON.stringify({prefix:document.getElementById('prefix').value,supervisor_role:document.getElementById('supervisor').value,promodemo_channel:document.getElementById('promodemo').value,audit_channel:document.getElementById('audit').value,embed_color:document.getElementById('embedColor').value,embed_footer:document.getElementById('footer').value,ticket_title:document.getElementById('ticketTitle').value,ticket_description:document.getElementById('ticketDescription').value,daily_min:Number(document.getElementById('dailyMin').value),daily_max:Number(document.getElementById('dailyMax').value),work_min:Number(document.getElementById('workMin').value),work_max:Number(document.getElementById('workMax').value),work_cooldown:Number(document.getElementById('workCooldown').value)})});statusBox.textContent='Settings saved.'}catch(e){statusBox.textContent=e.message}}
async function postPanel(){const channel=document.getElementById('ticketChannel').value;if(!channel){statusBox.textContent='Choose a ticket panel channel first.';return}statusBox.textContent='Posting…';try{await api('/api/guild/'+guildSelect.value+'/ticket-panel',{method:'POST',body:JSON.stringify({channel_id:channel})});statusBox.textContent='Ticket dropdown posted.'}catch(e){statusBox.textContent=e.message}}
function updatePreview(){const title=document.getElementById('customTitle').value,description=document.getElementById('customDescription').value;document.getElementById('preview').textContent=(title?'◆ '+title+'\n':'')+(description||'Embed preview will appear here.');document.getElementById('preview').style.borderColor=document.getElementById('customColor').value}
['customTitle','customDescription','customColor'].forEach(id=>document.getElementById(id).addEventListener('input',updatePreview));
async function sendEmbed(){const channel=document.getElementById('embedChannel').value;if(!channel){document.getElementById('embedStatus').textContent='Choose a channel first.';return}const fields=document.getElementById('customFields').value.split('\n').map(x=>x.trim()).filter(Boolean).map(line=>{const p=line.split('|');return{name:(p[0]||'').trim(),value:(p[1]||'').trim(),inline:(p[2]||'').trim().toLowerCase()==='true'}});const box=document.getElementById('embedStatus');box.textContent='Sending…';try{await api('/api/guild/'+guildSelect.value+'/embed',{method:'POST',body:JSON.stringify({channel_id:channel,title:document.getElementById('customTitle').value,description:document.getElementById('customDescription').value,color:document.getElementById('customColor').value,footer:document.getElementById('customFooter').value,author:document.getElementById('customAuthor').value,title_url:document.getElementById('customUrl').value,image_url:document.getElementById('customImage').value,thumbnail_url:document.getElementById('customThumb').value,fields})});box.textContent='Embed sent.'}catch(e){box.textContent=e.message}}
async function manageMoney(){const box=document.getElementById('moneyStatus');box.textContent='Saving…';try{await api('/api/guild/'+guildSelect.value+'/money',{method:'POST',body:JSON.stringify({user_id:document.getElementById('moneyUser').value,action:document.getElementById('moneyAction').value,amount:Number(document.getElementById('moneyAmount').value)})});box.textContent='Wallet updated.'}catch(e){box.textContent=e.message}}
function clearShopForm(){for(const id of ['shopId','shopName','shopPrice','shopEmoji','shopDescription'])document.getElementById(id).value='';document.getElementById('shopId').disabled=false}
function renderShopItems(items){const box=document.getElementById('shopItems');box.replaceChildren();if(!items.length){const empty=document.createElement('p');empty.className='small';empty.textContent='No shop items yet. Add the first one above.';box.append(empty);return}for(const item of items){const row=document.createElement('div');row.className='shop-item';const info=document.createElement('div');const title=document.createElement('strong');title.textContent=(item.emoji||'🛍️')+' '+item.name;const detail=document.createElement('div');detail.className='small';detail.textContent=item.id+' · '+(item.description||'No description');info.append(title,detail);const actions=document.createElement('div');actions.className='row';const price=document.createElement('span');price.className='shop-price';price.textContent=Number(item.price).toLocaleString()+' coins';const edit=document.createElement('button');edit.className='secondary';edit.textContent='Edit';edit.onclick=()=>{document.getElementById('shopId').value=item.id;document.getElementById('shopId').disabled=true;document.getElementById('shopName').value=item.name;document.getElementById('shopPrice').value=item.price;document.getElementById('shopEmoji').value=item.emoji||'';document.getElementById('shopDescription').value=item.description||'';document.getElementById('shopCard').scrollIntoView({behavior:'smooth'})};const del=document.createElement('button');del.className='secondary';del.textContent='Delete';del.onclick=()=>deleteShopItem(item.id);actions.append(price,edit,del);row.append(info,actions);box.append(row)}}
async function saveShopItem(){const box=document.getElementById('shopStatus');box.textContent='Saving item…';try{const d=await api('/api/guild/'+guildSelect.value+'/shop',{method:'POST',body:JSON.stringify({action:'save',id:document.getElementById('shopId').value,name:document.getElementById('shopName').value,price:Number(document.getElementById('shopPrice').value),emoji:document.getElementById('shopEmoji').value,description:document.getElementById('shopDescription').value})});renderShopItems(d.items);box.textContent='Shop item saved.';clearShopForm()}catch(e){box.textContent=e.message}}
async function deleteShopItem(id){const box=document.getElementById('shopStatus');box.textContent='Removing item…';try{const d=await api('/api/guild/'+guildSelect.value+'/shop',{method:'POST',body:JSON.stringify({action:'delete',id})});renderShopItems(d.items);box.textContent='Shop item removed.'}catch(e){box.textContent=e.message}}async function saveActivity(){const box=document.getElementById('activityStatus');box.textContent='Saving…';try{await api('/api/activity',{method:'POST',body:JSON.stringify({type:document.getElementById('activityType').value,text:document.getElementById('activityText').value})});box.textContent='Activity updated.'}catch(e){box.textContent=e.message}}
async function logout(){await fetch('/logout',{method:'POST',credentials:'same-origin'});location.href='/'}loadGuilds();
</script></body></html>"""
LANDING_HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Supreme Bot</title><style>*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 15% 5%,#55429c 0,transparent 40%),radial-gradient(ellipse at 90% 90%,#106566 0,transparent 38%),#080b16;color:#f6f5ff;font:16px/1.6 Inter,system-ui,sans-serif;min-height:100vh;display:grid;place-items:center;padding:22px}.card{position:relative;overflow:hidden;width:min(100%,700px);margin:20px;padding:clamp(28px,6vw,56px);background:linear-gradient(140deg,#1c2240ed,#10182bec 72%,#123035ed);border:1px solid #b9aaff42;border-radius:28px;box-shadow:0 30px 100px #0009,0 0 55px #987dff1a;backdrop-filter:blur(18px)}.card:after{content:'✦';position:absolute;right:5%;top:-100px;color:#e2dcff0b;font-size:300px;pointer-events:none}.card>div{position:relative;z-index:1;color:#c5b8ff;font-size:11px;font-weight:850;letter-spacing:.16em}.card h1{position:relative;z-index:1;font-size:clamp(38px,7vw,64px);line-height:1.02;letter-spacing:-.05em;margin:22px 0 16px}.card p{position:relative;z-index:1;color:#bdc6dc;line-height:1.75}.button{position:relative;z-index:1;display:inline-flex;background:linear-gradient(120deg,#b09aff,#8b72ef);color:#151026;padding:14px 21px;border:1px solid #d9cdff55;border-radius:13px;font-weight:850;text-decoration:none;box-shadow:0 10px 30px #8d70e944;transition:.2s}.button:hover{transform:translateY(-2px);filter:brightness(1.08)}.note{font-size:13px;margin-top:24px;padding-top:17px;border-top:1px solid #ffffff19}</style></head><body><main class="card"><div>SUPREME BOT • DASHBOARD</div><h1>Configure your server</h1><p>Sign in with Discord to manage server settings. Only the bot owner and trusted extra owners can enter the dashboard.</p><a class="button" href="/login">Continue with Discord</a><p class="note">The bot must already be invited to your server. Set DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, and DISCORD_REDIRECT_URI in the hosting environment to enable sign-in.</p></main></body></html>"""


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

    candidate_session = {"user": {"id": str(user["id"])}, "guilds": guilds}
    if not any(web_user_can_manage(candidate_session, info.get("id")) for info in guilds):
        return web.Response(text="Dashboard access is limited to the bot owner and trusted extra owners.", status=403)

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
        "shop_items": get_shop_items(gid),
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


async def handle_api_shop(request):
    _, guild, error = await web_authorized_guild(request)
    if error:
        return error
    try:
        data = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest):
        return response_json_error("Invalid shop item data.")
    if not isinstance(data, dict):
        return response_json_error("Invalid shop item data.")
    action = str(data.get("action", ""))
    item_id = str(data.get("id", "")).strip().lower().replace(" ", "_")
    items = get_shop_items(guild.id)
    if not item_id or len(item_id) > 24 or not item_id.replace("_", "").isalnum():
        return response_json_error("Item ID must use letters, numbers, or underscores (up to 24 characters).")
    current = next((item for item in items if item.get("id") == item_id), None)
    if action == "delete":
        if not current:
            return response_json_error("That shop item does not exist.", 404)
        items.remove(current)
    elif action == "save":
        name = str(data.get("name", "")).strip()
        emoji = str(data.get("emoji", "")).strip()[:80]
        description = str(data.get("description", "")).strip()
        try:
            price = int(data.get("price", 0))
        except (TypeError, ValueError):
            return response_json_error("Price must be a whole number.")
        if not name or len(name) > 80 or len(description) > 200 or not 1 <= price <= 1000000000:
            return response_json_error("Add a name (1–80 chars), description (up to 200), and price (1–1,000,000,000).")
        item = {"id": item_id, "name": name, "price": price, "emoji": emoji, "description": description}
        if current:
            current.update(item)
        elif len(items) >= 100:
            return response_json_error("A server shop can have up to 100 items.")
        else:
            items.append(item)
    else:
        return response_json_error("Choose save or delete.")
    config.setdefault("shop_items", {})[str(guild.id)] = items
    if not save_config():
        return response_json_error("Shop item could not be saved to the bot's config file.", 500)
    return web.json_response({"ok": True, "items": items})


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
        return response_json_error("Could not send this embed.", 502)
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
    app.router.add_post("/api/guild/{guild_id}/shop", handle_api_shop)
    app.router.add_post("/api/guild/{guild_id}/ticket-panel", handle_api_ticket_panel)
    app.router.add_post("/api/guild/{guild_id}/embed", handle_api_embed)
    app.router.add_post("/api/activity", handle_api_activity)
    app.router.add_post("/api/guild/{guild_id}/money", handle_api_money)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info("Supreme Bot dashboard started on 0.0.0.0:%s", PORT)

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

EMOJI_SOURCES = dict(EMOJIS)

async def install_application_emojis():
    fetch_emojis = getattr(bot, "fetch_application_emojis", None)
    create_emoji = getattr(bot, "create_application_emoji", None)
    if not callable(fetch_emojis) or not callable(create_emoji):
        return
    try:
        existing = {emoji.name: emoji for emoji in await fetch_emojis()}
    except Exception:
        return
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "emojis")
    os.makedirs(folder, exist_ok=True)
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
                    with open(image_path, "wb") as image_file:
                        image_file.write(image_data)
                created = await create_emoji(name=name, image=image_data)
                EMOJIS[name] = str(created)
            except Exception:
                pass

config = {
    "supervisor_roles": {}, "promodemo_channels": {}, "audit_channels": {},
    "rank_ladders": {}, "staff_limits": {}, "economy": {}, "extra_owners": {},
    "activity": {}, "prefixes": {}, "embed_settings": {}, "ticket_settings": {},
    "economy_settings": {}, "shop_items": {}, "economy_no_cooldown": {},
    "blacklists": {}, "disabled_guilds": {}, "ai_tasks": {}, "ai_channels": {}
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
        pass


def save_config():
    temporary_file = CONFIG_FILE + ".tmp"
    try:
        with open(temporary_file, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
        os.replace(temporary_file, CONFIG_FILE)
        return True
    except OSError:
        return False


def economy_account(guild_id, user_id):
    guild_accounts = config.setdefault("economy", {}).setdefault(str(guild_id), {})
    account = guild_accounts.setdefault(str(user_id), {"balance": 0, "last_daily": 0, "last_work": 0})
    account["balance"] = max(0, int(account.get("balance", 0)))
    account.setdefault("last_daily", 0)
    account.setdefault("last_work", 0)
    account["bank"] = max(0, int(account.get("bank", 0)))
    if not isinstance(account.get("inventory"), dict): account["inventory"] = {}
    if not isinstance(account.get("cooldowns"), dict): account["cooldowns"] = {}
    account["daily_streak"] = max(0, int(account.get("daily_streak", 0)))
    if not isinstance(account.get("stats"), dict): account["stats"] = {}
    for stat in ("earned", "spent", "worked"): account["stats"].setdefault(stat, 0)
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


def get_shop_items(guild_id):
    items = config.setdefault("shop_items", {}).setdefault(str(guild_id), [])
    if not isinstance(items, list):
        items = []
        config["shop_items"][str(guild_id)] = items
    return items


def refresh_shop_items(guild_id):
    gid = str(guild_id)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
        shops = saved.get("shop_items", {})
        if isinstance(shops, dict) and gid in shops and isinstance(shops[gid], list):
            config.setdefault("shop_items", {})[gid] = shops[gid]
    except Exception:
        pass
    return get_shop_items(guild_id)


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
# PERMISSION & CHECKS
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
    now = time.time()
    user_id = str(ctx.author.id)
    if "staff_limits" not in config: config["staff_limits"] = {}
    if user_id not in config["staff_limits"]: config["staff_limits"][user_id] = {"kicks": [], "bans": []}
    timestamps = [t for t in config["staff_limits"][user_id].get(action_type, []) if now - t < 86400]
    if len(timestamps) >= limit: return False, len(timestamps)
    timestamps.append(now)
    config["staff_limits"][user_id][action_type] = timestamps
    save_config()
    return True, len(timestamps)


async def audit(guild, message):
    channel_id = guild_setting("audit_channels", guild.id)
    if not channel_id: return
    channel = guild.get_channel(int(channel_id))
    if channel:
        try: await channel.send(message, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException: pass


# =========================
# TICKET VIEWS
# =========================

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{EMOJIS['warning']} Closing ticket in 5 seconds...", ephemeral=False)
        await audit(interaction.guild, f"Ticket closed by {interaction.user} | Channel: {interaction.channel.name}")
        await asyncio.sleep(5)
        try: await interaction.channel.delete(reason=f"Closed by {interaction.user}")
        except discord.HTTPException: pass


class TicketSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Choose a ticket type...", min_values=1, max_values=1, custom_id="ticket_type_select",
        options=[
            discord.SelectOption(label="General Support", value="support", description="Ask the team for help", emoji="🎟️"),
            discord.SelectOption(label="Report a Member", value="report", description="Privately report a server issue", emoji="🚩"),
            discord.SelectOption(label="Other Question", value="other", description="Contact the staff team", emoji="💬"),
        ]
    )
    async def create_ticket(self, interaction: discord.Interaction, select: discord.ui.Select):
        guild, member, ticket_type = interaction.guild, interaction.user, select.values[0]
        channel_name = f"ticket-{ticket_type}-{member.id}"
        if discord.utils.get(guild.text_channels, name=channel_name):
            return await interaction.response.send_message(f"{EMOJIS['error']} You already have this ticket open.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        category = discord.utils.get(guild.categories, name="Support Tickets") or await guild.create_category("Support Tickets")
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        embed = discord.Embed(title=f"{EMOJIS['ticket']} {ticket_type.title()} Ticket", description=f"Hello {member.mention}! Support staff will be with you shortly.", color=discord.Color.blue())
        apply_embed_theme(guild.id, embed)
        await channel.send(embed=embed, view=TicketCloseView())
        await interaction.followup.send(f"{EMOJIS['success']} Your ticket is ready: {channel.mention}", ephemeral=True)


# =========================
# GENERAL / MOD COMMANDS
# =========================

@bot.command(name="ping")
@commands.guild_only()
async def ping(ctx):
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Pong! Latency: `{round(bot.latency * 1000)}ms`", color=discord.Color.blue()))


@bot.command(name="serverinfo")
@commands.guild_only()
async def serverinfo(ctx):
    g = ctx.guild
    embed = discord.Embed(title=f"{EMOJIS['gear']} {g.name} Information", color=discord.Color.blurple())
    embed.add_field(name="Owner", value=g.owner, inline=True)
    embed.add_field(name="Members", value=g.member_count, inline=True)
    await ctx.reply(embed=embed)


@bot.command(name="userinfo")
@commands.guild_only()
async def userinfo(ctx, member: discord.Member = None):
    m = member or ctx.author
    embed = discord.Embed(title=f"{EMOJIS['user']} {m} Info", color=m.color)
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="ID", value=m.id, inline=True)
    await ctx.reply(embed=embed)


@bot.command(name="avatar")
@commands.guild_only()
async def avatar(ctx, member: discord.Member = None):
    m = member or ctx.author
    embed = discord.Embed(title=f"Avatar for {m}", color=discord.Color.blurple())
    embed.set_image(url=m.display_avatar.url)
    await ctx.reply(embed=embed)


@bot.command(name="kick")
@commands.guild_only()
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if not user_is_staff(ctx): return
    await member.kick(reason=reason)
    await ctx.reply(embed=discord.Embed(description=f"Kicked {member.mention}", color=discord.Color.orange()))


@bot.command(name="ban")
@commands.guild_only()
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if not user_is_staff(ctx): return
    await member.ban(reason=reason)
    await ctx.reply(embed=discord.Embed(description=f"Banned {member.mention}", color=discord.Color.red()))


@bot.command(name="clear")
@commands.guild_only()
async def clear(ctx, amount: int = 5):
    if not user_is_staff(ctx): return
    await ctx.channel.purge(limit=amount + 1)


@bot.command(name="mute")
@commands.guild_only()
async def mute(ctx, member: discord.Member, *, reason="No reason provided"):
    if not user_is_staff(ctx): return
    from datetime import timedelta
    await member.timeout(timedelta(minutes=10), reason=reason)
    await ctx.reply(embed=discord.Embed(description=f"Timed out {member.mention}", color=discord.Color.orange()))


# =========================
# HUGGING FACE AI INTEGRATION
# =========================

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "").strip()
HF_MODEL = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.3-70B-Instruct").strip()
AI_HISTORY = {}
AI_LAST_REQUEST = {}

async def call_ai(guild_id, user_id, prompt):
    if not HF_API_KEY:
        raise RuntimeError("AI is not configured yet. Set HUGGINGFACE_API_KEY in the hosting environment variables.")
    
    history_key = (int(guild_id), int(user_id))
    history = AI_HISTORY.get(history_key, [])[-6:]
    
    messages = [
        {"role": "system", "content": "You are Supreme Bot AI, a friendly, helpful AI assistant chatting in a Discord server. Keep responses concise, structured, and helpful."}
    ]
    for turn in history: messages.append(turn)
    messages.append({"role": "user", "content": prompt})

    payload = {"model": HF_MODEL, "messages": messages, "max_tokens": 500, "temperature": 0.7}
    headers = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}

    timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post("https://router.huggingface.co/v1/chat/completions", headers=headers, json=payload) as response:
            if response.status >= 400:
                if response.status == 401: raise RuntimeError("Hugging Face API key was rejected. Check your token.")
                if response.status == 429: raise RuntimeError("Hugging Face rate limit reached or model loading. Try again shortly.")
                raise RuntimeError("The AI service returned an error. Try again later.")
            data = await response.json()

    try: answer = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError): raise RuntimeError("Unexpected AI response format.")

    AI_HISTORY[history_key] = history + [{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}]
    return answer


@bot.command(name="ask")
@commands.guild_only()
async def ask_ai(ctx, *, prompt: str):
    """Chat with Hugging Face AI."""
    prompt = prompt.strip()
    if not prompt: return await ctx.reply("Ask me something, e.g. `>ask how do black holes work`", mention_author=False)
    
    key = (ctx.guild.id, ctx.author.id)
    now = time.monotonic()
    wait = 4 - (now - AI_LAST_REQUEST.get(key, 0))
    if wait > 0: return await ctx.reply(f"Please wait {wait:.1f}s before your next message.", mention_author=False)
    AI_LAST_REQUEST[key] = now

    async with ctx.typing():
        try: answer = await call_ai(ctx.guild.id, ctx.author.id, prompt)
        except Exception as exc: return await ctx.reply(str(exc), mention_author=False)

    for start in range(0, len(answer), 1900):
        await ctx.reply(answer[start:start + 1900], mention_author=False, allowed_mentions=discord.AllowedMentions.none())


@bot.command(name="clearai", aliases=["resetai"])
@commands.guild_only()
async def clear_ai_history(ctx):
    """Clear your AI conversation history."""
    AI_HISTORY.pop((ctx.guild.id, ctx.author.id), None)
    await ctx.reply("Your AI chat history has been cleared.", mention_author=False)


@bot.command(name="dashboard")
async def dashboard_cmd(ctx):
    embed = discord.Embed(title="Supreme Bot Dashboard", url=DASHBOARD_URL, description=f"Open the [dashboard]({DASHBOARD_URL}) to configure your server.", color=discord.Color.blurple())
    await ctx.reply(embed=embed, mention_author=False)


@bot.command(name="help")
async def help_command(ctx):
    prefix = get_server_prefix(ctx.guild.id if ctx.guild else None)
    embed = discord.Embed(title="Supreme Bot • Help", description=f"Prefix: `{prefix}`", color=discord.Color.blurple())
    embed.add_field(name="🤖 AI Commands", value=f"`{prefix}ask <prompt>`, `{prefix}clearai`", inline=False)
    embed.add_field(name="🛡️ Moderation", value=f"`{prefix}kick`, `{prefix}ban`, `{prefix}mute`, `{prefix}clear`", inline=False)
    await ctx.reply(embed=embed, mention_author=False)


@bot.event
async def on_message(message):
    if message.author.bot: return
    ctx = await bot.get_context(message)
    await bot.process_commands(message)


@bot.event
async def on_ready():
    bot.add_view(TicketSetupView())
    bot.add_view(TicketCloseView())
    await install_application_emojis()
    if not getattr(bot, "_slash_commands_synced", False):
        try:
            await bot.tree.sync()
            bot._slash_commands_synced = True
        except Exception:
            pass
    logging.info("Supreme logged in as %s", bot.user)


async def main():
    load_config()
    asyncio.create_task(start_web_server())
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())








