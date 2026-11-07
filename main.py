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
    # Discord server permissions do not grant dashboard access. Only the bot owner
    # and explicitly trusted extra owners can administer it.
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
        return response_json_error("Shop item could not be saved to the bot's config file. Check that the dashboard and bot share the same deployment and writable config path.", 500)
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
    app.router.add_post("/api/guild/{guild_id}/shop", handle_api_shop)
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
    "economy_settings": {},
    "shop_items": {},
    "economy_no_cooldown": {},
    "blacklists": {},
    "disabled_guilds": {},
    "ai_tasks": {},
    "ai_channels": {}
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
    """Read the persisted shop catalog before displaying it, if available."""
    gid = str(guild_id)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
        shops = saved.get("shop_items", {})
        if isinstance(shops, dict) and gid in shops and isinstance(shops[gid], list):
            config.setdefault("shop_items", {})[gid] = shops[gid]
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, OSError):
        logging.exception("Could not refresh persisted shop catalog")
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

ECONOMY_SPAM_TRACKER = {}
ECONOMY_SPAM_WINDOW_SECONDS = 10
ECONOMY_SPAM_COMMAND_LIMIT = 5


class EconomyChannelOnly(commands.CheckFailure):
    pass


class EconomySpamTriggered(commands.CheckFailure):
    pass


def record_economy_command(guild_id, user_id):
    key = (int(guild_id), int(user_id))
    now = time.monotonic()
    recent = [stamp for stamp in ECONOMY_SPAM_TRACKER.get(key, []) if now - stamp < ECONOMY_SPAM_WINDOW_SECONDS]
    recent.append(now)
    if len(recent) >= ECONOMY_SPAM_COMMAND_LIMIT:
        ECONOMY_SPAM_TRACKER.pop(key, None)
        account = economy_account(guild_id, user_id)
        removed = int(account.get("balance", 0)) + int(account.get("bank", 0))
        account["balance"] = 0
        account["bank"] = 0
        save_config()
        return True, removed
    ECONOMY_SPAM_TRACKER[key] = recent
    return False, 0


async def economy_command_guard(ctx):
    if ctx.guild is None or ctx.channel.id != ECONOMY_CHANNEL_ID:
        raise EconomyChannelOnly()
    triggered, removed = record_economy_command(ctx.guild.id, ctx.author.id)
    if triggered:
        await audit(ctx.guild, f"Economy spam protection reset wallet and bank for {ctx.author.id}; removed {removed:,} coins")
        await ctx.reply(embed=economy_embed(f"Spam protection triggered: you used 5 economy commands within 10 seconds. Your wallet and bank were reset (**{removed:,}** coins removed)."), mention_author=False)
        raise EconomySpamTriggered()
    return True

@bot.command(name="balance", aliases=["bal"])
@commands.guild_only()
@commands.check(economy_command_guard)
async def balance(ctx, member: discord.Member = None):
    """Check your own or another member's wallet."""
    member = member or ctx.author
    account = economy_account(ctx.guild.id, member.id)
    await ctx.reply(embed=economy_embed(f"**{member.display_name}** has **{account['balance']:,}** coins."))


@bot.command(name="daily")
@commands.guild_only()
@commands.check(economy_command_guard)
async def daily(ctx):
    """Claim a once-per-day coin reward."""
    import time
    account = economy_account(ctx.guild.id, ctx.author.id)
    remaining = 0 if economy_has_cooldown_immunity(ctx) else 86400 - (int(time.time()) - int(account.get("last_daily", 0)))
    if remaining > 0:
        hours, minutes = divmod(remaining, 3600)
        await ctx.reply(embed=economy_embed(f"Your next daily reward is ready in **{hours}h {minutes // 60}m**."))
        return
    economy_settings = get_economy_settings(ctx.guild.id)
    reward = random.randint(int(economy_settings["daily_min"]), int(economy_settings["daily_max"]))
    account["balance"] += reward
    account.setdefault("stats", {}).setdefault("earned", 0)
    account["stats"]["earned"] += reward
    elapsed_since_daily = int(time.time()) - int(account.get("last_daily", 0))
    if not account.get("last_daily", 0) or elapsed_since_daily > 172800:
        account["daily_streak"] = 1
    elif elapsed_since_daily >= 86400:
        account["daily_streak"] = int(account.get("daily_streak", 0)) + 1
    account["last_daily"] = int(time.time())
    save_config()
    await ctx.reply(embed=economy_embed(f"Daily reward claimed! You received **{reward}** coins. Balance: **{account['balance']:,}**."))


@bot.command(name="work", aliases=["job"])
@commands.guild_only()
@commands.check(economy_command_guard)
async def work(ctx):
    """Work for a random coin reward; 60-second cooldown."""
    import time
    account = economy_account(ctx.guild.id, ctx.author.id)
    economy_settings = get_economy_settings(ctx.guild.id)
    remaining = 0 if economy_has_cooldown_immunity(ctx) else int(economy_settings["work_cooldown"]) - (int(time.time()) - int(account.get("last_work", 0)))
    if remaining > 0:
        await ctx.reply(embed=economy_embed(f"Catch your breath! You can work again in **{remaining}s**."))
        return
    reward = random.randint(int(economy_settings["work_min"]), int(economy_settings["work_max"]))
    jobs = ["delivered a dragon's lunch", "organized a wizard's bookshelf", "DJ'd a tiny robot party", "found a pile of coins", "walked a very polite dinosaur"]
    account["balance"] += reward
    account["stats"]["earned"] += reward
    account["stats"]["worked"] = int(account["stats"].get("worked", 0)) + 1
    account["last_work"] = int(time.time())
    save_config()
    await ctx.reply(embed=economy_embed(f"You {random.choice(jobs)} and earned **{reward}** coins. Balance: **{account['balance']:,}**."))


@bot.command(name="pay", aliases=["transfer"])
@commands.guild_only()
@commands.check(economy_command_guard)
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
@commands.check(economy_command_guard)
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


@bot.command(name="nocooldown")
@commands.guild_only()
@commands.check(economy_command_guard)
async def nocooldown(ctx, member: discord.Member):
    """Owner: let a member skip all economy cooldowns and protect them from rob."""
    if not user_is_owner(ctx):
        return await ctx.reply(embed=economy_embed("Only the bot owner, server owner, or an extra owner can grant this."))
    guild_id = str(ctx.guild.id)
    grants = config.setdefault("economy_no_cooldown", {}).setdefault(guild_id, [])
    if str(member.id) in {str(user_id) for user_id in grants}:
        return await ctx.reply(embed=economy_embed(f"{member.mention} already has economy cooldown immunity."))
    grants.append(str(member.id))
    save_config()
    await audit(ctx.guild, f"Economy cooldown immunity granted by {ctx.author.id} to {member.id}")
    await ctx.reply(embed=economy_embed(f"Granted {member.mention} no economy cooldowns and robbery protection."))


@bot.command(name="removenocooldown", aliases=["cooldown"])
@commands.guild_only()
@commands.check(economy_command_guard)
async def removenocooldown(ctx, member: discord.Member):
    """Owner: remove a member's granted economy cooldown immunity."""
    if not user_is_owner(ctx):
        return await ctx.reply(embed=economy_embed("Only the bot owner, server owner, or an extra owner can remove this."))
    guild_id = str(ctx.guild.id)
    grants = config.setdefault("economy_no_cooldown", {}).setdefault(guild_id, [])
    if str(member.id) not in {str(user_id) for user_id in grants}:
        return await ctx.reply(embed=economy_embed(f"{member.mention} does not have a granted cooldown exemption."))
    config["economy_no_cooldown"][guild_id] = [str(user_id) for user_id in grants if str(user_id) != str(member.id)]
    save_config()
    await audit(ctx.guild, f"Economy cooldown immunity removed by {ctx.author.id} from {member.id}")
    await ctx.reply(embed=economy_embed(f"Removed the economy cooldown exemption from {member.mention}."))


@bot.command(name="addmoney", aliases=["addcoins"])
@commands.guild_only()
@commands.check(economy_command_guard)
async def addmoney(ctx, target: str, amount: int):
    """Admin: add coins to one member or all server members' wallets."""
    if not await require_economy_admin(ctx): return
    if not 1 <= amount <= 1000000000:
        await ctx.reply(embed=economy_embed("Amount must be from 1 to 1,000,000,000.")); return
    if target.lower() == "all":
        members = {}
        try:
            async for guild_member in ctx.guild.fetch_members(limit=None):
                if not guild_member.bot:
                    members[guild_member.id] = guild_member
        except discord.HTTPException:
            return await ctx.reply(embed=economy_embed("I couldn't retrieve the full member list. Check the Server Members Intent and try again; no wallets were changed."))
        if not members:
            return await ctx.reply(embed=economy_embed("There are no member wallets to update."))
        for user_id, member in members.items():
            account = economy_account(ctx.guild.id, user_id)
            account["balance"] += amount
            account.setdefault("stats", {}).setdefault("earned", 0)
            account["stats"]["earned"] += amount
        save_config()
        await audit(ctx.guild, f"Bulk addmoney by {ctx.author.id}: +{amount:,} coins for {len(members)} wallets")
        return await ctx.reply(embed=economy_embed(f"Added **{amount:,}** coins to **{len(members):,}** member wallets."))
    try:
        member = await commands.MemberConverter().convert(ctx, target)
    except commands.BadArgument:
        return await ctx.reply(embed=economy_embed("Mention a server member or use `all`."))
    account = economy_account(ctx.guild.id, member.id)
    account["balance"] += amount
    account.setdefault("stats", {}).setdefault("earned", 0)
    account["stats"]["earned"] += amount
    save_config()
    await ctx.reply(embed=economy_embed(f"Added **{amount:,}** coins to {member.mention}. New balance: **{account['balance']:,}**."))


@bot.command(name="removemoney", aliases=["removecoins"])
@commands.guild_only()
@commands.check(economy_command_guard)
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
@commands.check(economy_command_guard)
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
@commands.check(economy_command_guard)
async def resetmoney(ctx, member: discord.Member = None):
    """Admin: reset one member's wallet."""
    if not await require_economy_admin(ctx): return
    if not member:
        return await ctx.reply(embed=economy_embed("Mention one member, or confirm a full reset with `reseteconomy all`."))
    account = economy_account(ctx.guild.id, member.id)
    account.update({"balance": 0, "last_daily": 0, "last_work": 0, "bank": 0, "inventory": {}, "daily_streak": 0})
    message = f"Reset {member.mention}'s wallet, bank, and inventory."
    save_config()
    await ctx.reply(embed=economy_embed(message, discord.Color.orange()))


@bot.command(name="reseteconomy")
@commands.guild_only()
@commands.check(economy_command_guard)
async def reseteconomy(ctx, target: str):
    """Admin: reset every wallet, bank, and inventory in the server."""
    if not await require_economy_admin(ctx):
        return
    if target.lower() != "all":
        return await ctx.reply(embed=economy_embed("Confirm a full server reset with `reseteconomy all`."))
    accounts = config.setdefault("economy", {}).setdefault(str(ctx.guild.id), {})
    count = len(accounts)
    accounts.clear()
    save_config()
    await audit(ctx.guild, f"Full economy reset by {ctx.author.id}: cleared {count} wallets")
    await ctx.reply(embed=economy_embed(f"Reset the entire server economy: **{count:,}** saved wallets cleared. Shop items and economy settings were kept.", discord.Color.orange()))


# Shared economy helpers. Every cooldown and item count is stored in config.json.
def economy_has_cooldown_immunity(ctx, member=None):
    member = member or ctx.author
    guild_id = str(ctx.guild.id)
    trusted_owners = {str(uid) for uid in config.get("extra_owners", {}).get(guild_id, [])}
    no_cooldown = {str(uid) for uid in config.get("economy_no_cooldown", {}).get(guild_id, [])}
    return (member.id == OWNER_ID or member.id == ctx.guild.owner_id
            or str(member.id) in trusted_owners or str(member.id) in no_cooldown)


def economy_cooldown_remaining(account, key, seconds, ctx=None):
    if ctx and economy_has_cooldown_immunity(ctx):
        return 0
    return max(0, int(seconds) - (int(time.time()) - int(account.setdefault("cooldowns", {}).get(key, 0))))


def economy_mark_cooldown(account, key):
    account.setdefault("cooldowns", {})[key] = int(time.time())


def economy_add(account, amount):
    amount = int(amount)
    account["balance"] += amount
    account.setdefault("stats", {}).setdefault("earned", 0)
    account["stats"]["earned"] += amount


def economy_item(items, query):
    query = str(query).strip().lower()
    return next((item for item in items if item.get("id", "").lower() == query or item.get("name", "").lower() == query), None)


def parse_amount(value, account):
    return int(account["balance"]) if str(value).lower() == "all" else int(value)


@bot.command(name="bank", aliases=["vault"])
@commands.guild_only()
@commands.check(economy_command_guard)
async def bank(ctx, member: discord.Member = None):
    member = member or ctx.author
    a = economy_account(ctx.guild.id, member.id)
    await ctx.reply(embed=economy_embed(f"**{member.display_name}** — wallet **{a['balance']:,}**, bank **{a['bank']:,}**, total **{a['balance'] + a['bank']:,}** coins."))


@bot.command(name="deposit")
@commands.guild_only()
@commands.check(economy_command_guard)
async def deposit(ctx, amount: str):
    a = economy_account(ctx.guild.id, ctx.author.id)
    try: amount = parse_amount(amount, a)
    except ValueError: amount = 0
    if not 1 <= amount <= a["balance"]:
        return await ctx.reply(embed=economy_embed("Choose an amount you have, or use `all`."))
    a["balance"] -= amount; a["bank"] += amount; save_config()
    await ctx.reply(embed=economy_embed(f"Deposited **{amount:,}** coins. Bank: **{a['bank']:,}**."))


@bot.command(name="withdraw")
@commands.guild_only()
@commands.check(economy_command_guard)
async def withdraw(ctx, amount: str):
    a = economy_account(ctx.guild.id, ctx.author.id)
    try: amount = parse_amount(amount, {"balance": a["bank"]})
    except ValueError: amount = 0
    if not 1 <= amount <= a["bank"]:
        return await ctx.reply(embed=economy_embed("Choose an amount in your bank, or use `all`."))
    a["bank"] -= amount; a["balance"] += amount; save_config()
    await ctx.reply(embed=economy_embed(f"Withdrew **{amount:,}** coins. Wallet: **{a['balance']:,}**."))


@bot.command(name="weekly")
@commands.guild_only()
@commands.check(economy_command_guard)
async def weekly(ctx):
    a = economy_account(ctx.guild.id, ctx.author.id); wait = economy_cooldown_remaining(a, "weekly", 604800, ctx)
    if wait: return await ctx.reply(embed=economy_embed(f"Weekly reward ready in **{wait // 86400}d {(wait % 86400) // 3600}h**."))
    reward = random.randint(500, 1200); economy_add(a, reward); economy_mark_cooldown(a, "weekly"); save_config()
    await ctx.reply(embed=economy_embed(f"Weekly bonus: **+{reward:,}** coins!"))


@bot.command(name="monthly")
@commands.guild_only()
@commands.check(economy_command_guard)
async def monthly(ctx):
    a = economy_account(ctx.guild.id, ctx.author.id); wait = economy_cooldown_remaining(a, "monthly", 2592000, ctx)
    if wait: return await ctx.reply(embed=economy_embed(f"Monthly reward ready in **{wait // 86400} days**."))
    reward = random.randint(2500, 6000); economy_add(a, reward); economy_mark_cooldown(a, "monthly"); save_config()
    await ctx.reply(embed=economy_embed(f"Monthly bonus: **+{reward:,}** coins!"))


async def timed_earn(ctx, key, seconds, low, high, success_text, failure_text=None, fail_chance=0):
    a = economy_account(ctx.guild.id, ctx.author.id); wait = economy_cooldown_remaining(a, key, seconds, ctx)
    if wait: return await ctx.reply(embed=economy_embed(f"Try again in **{wait}s**."))
    economy_mark_cooldown(a, key)
    if failure_text and random.random() < fail_chance:
        loss = min(a["balance"], random.randint(1, max(1, high // 2))); a["balance"] -= loss
        a.setdefault("stats", {}).setdefault("spent", 0); a["stats"]["spent"] += loss
        text = failure_text.format(loss=loss)
    else:
        reward = random.randint(low, high); economy_add(a, reward); text = success_text.format(reward=reward)
    save_config(); await ctx.reply(embed=economy_embed(text))


@bot.command(name="beg")
@commands.guild_only()
@commands.check(economy_command_guard)
async def beg(ctx):
    await timed_earn(ctx, "beg", 90, 5, 80, "A friendly stranger gave you **{reward}** coins.", "The guard caught you. You paid **{loss}** coins in fines.", .08)


@bot.command(name="hunt")
@commands.guild_only()
@commands.check(economy_command_guard)
async def hunt(ctx):
    await timed_earn(ctx, "hunt", 60, 25, 180, "Your hunt was a success! You earned **{reward}** coins.", "The forest ranger fined you **{loss}** coins.", .12)


@bot.command(name="fish")
@commands.guild_only()
@commands.check(economy_command_guard)
async def fish(ctx):
    await timed_earn(ctx, "fish", 45, 15, 140, "You caught a rare fish and sold it for **{reward}** coins.")


@bot.command(name="crime")
@commands.guild_only()
@commands.check(economy_command_guard)
async def crime(ctx):
    await timed_earn(ctx, "crime", 120, 70, 350, "The caper worked! You got **{reward}** coins.", "The plan went wrong and you lost **{loss}** coins.", .40)


@bot.command(name="rob")
@commands.guild_only()
@commands.check(economy_command_guard)
async def rob(ctx, member: discord.Member):
    if member.bot or member.id == ctx.author.id: return await ctx.reply(embed=economy_embed("Pick another human member."))
    if economy_has_cooldown_immunity(ctx, member): return await ctx.reply(embed=economy_embed("That member is protected from robbery."))
    a = economy_account(ctx.guild.id, ctx.author.id); target = economy_account(ctx.guild.id, member.id)
    wait = economy_cooldown_remaining(a, "rob", 300, ctx)
    if wait: return await ctx.reply(embed=economy_embed(f"The heat is high. Try again in **{wait}s**."))
    economy_mark_cooldown(a, "rob")
    if random.random() < .38 and target["balance"] > 0:
        amount = min(target["balance"], random.randint(1, max(1, target["balance"] // 3)))
        target["balance"] -= amount; economy_add(a, amount); result = f"You grabbed **{amount:,}** coins from {member.mention}!"
    else:
        fine = min(a["balance"], random.randint(20, 150)); a["balance"] -= fine; result = f"The attempt failed and you paid a **{fine:,}** coin fine."
    save_config(); await ctx.reply(embed=economy_embed(result))


@bot.command(name="profile", aliases=["economyprofile"])
@commands.guild_only()
@commands.check(economy_command_guard)
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author; a = economy_account(ctx.guild.id, member.id)
    embed = discord.Embed(title=f"{member.display_name}'s Coin Profile", color=discord.Color.blurple())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Wallet", value=f"{EMOJIS['money']} {a['balance']:,}")
    embed.add_field(name="Bank", value=f"{EMOJIS['money']} {a['bank']:,}")
    embed.add_field(name="Lifetime earned", value=f"{a['stats'].get('earned', 0):,}")
    embed.add_field(name="Daily streak", value=str(a.get("daily_streak", 0)))
    await ctx.reply(embed=embed)


@bot.command(name="inventory", aliases=["inv"])
@commands.guild_only()
@commands.check(economy_command_guard)
async def inventory(ctx, member: discord.Member = None):
    member = member or ctx.author; a = economy_account(ctx.guild.id, member.id); lines=[]
    for item_id, qty in a["inventory"].items():
        item = economy_item(refresh_shop_items(ctx.guild.id), item_id)
        lines.append(f"{(item or {}).get('emoji', '📦')} **{(item or {}).get('name', item_id)}** × {qty}")
    await ctx.reply(embed=economy_embed("\n".join(lines) if lines else f"{member.display_name}'s inventory is empty."))


@bot.command(name="shop", aliases=["store"])
@commands.guild_only()
@commands.check(economy_command_guard)
async def shop(ctx):
    items = refresh_shop_items(ctx.guild.id)
    if not items: return await ctx.reply(embed=economy_embed(f"No shop items are saved for this server (**{ctx.guild.id}**). Select this exact server in the dashboard, and make sure the dashboard and bot run in the same deployment/config."))
    embed = discord.Embed(title="Supreme Shop", description="Buy with `buy <item-id> [quantity]` · sell back with `sell <item-id> [quantity]`", color=discord.Color.blurple())
    for item in items[:10]: embed.add_field(name=f"{item.get('emoji', '🛍️')} {item['name']} · {int(item['price']):,}", value=f"`{item['id']}` — {item.get('description') or 'A special shop item.'}", inline=False)
    await ctx.reply(embed=embed)


@bot.command(name="buy")
@commands.guild_only()
@commands.check(economy_command_guard)
async def buy(ctx, item_id: str, quantity: int = 1):
    item = economy_item(refresh_shop_items(ctx.guild.id), item_id)
    if not item: return await ctx.reply(embed=economy_embed("Item not found. Check `shop` for item IDs."))
    if not 1 <= quantity <= 100: return await ctx.reply(embed=economy_embed("Quantity must be from 1 to 100."))
    a = economy_account(ctx.guild.id, ctx.author.id); price = int(item["price"]) * quantity
    if a["balance"] < price: return await ctx.reply(embed=economy_embed(f"You need **{price - a['balance']:,}** more coins."))
    a["balance"] -= price; a["inventory"][item["id"]] = int(a["inventory"].get(item["id"], 0)) + quantity
    a["stats"]["spent"] = int(a["stats"].get("spent", 0)) + price; save_config()
    await ctx.reply(embed=economy_embed(f"Bought {item.get('emoji', '🛍️')} **{item['name']} × {quantity}** for **{price:,}** coins."))


@bot.command(name="sell")
@commands.guild_only()
@commands.check(economy_command_guard)
async def sell(ctx, item_id: str, quantity: int = 1):
    item = economy_item(refresh_shop_items(ctx.guild.id), item_id)
    if not item: return await ctx.reply(embed=economy_embed("Item not found in the server shop."))
    a = economy_account(ctx.guild.id, ctx.author.id); owned = int(a["inventory"].get(item["id"], 0))
    if not 1 <= quantity <= owned: return await ctx.reply(embed=economy_embed(f"You own **{owned}** of that item."))
    a["inventory"][item["id"]] = owned - quantity
    if not a["inventory"][item["id"]]: a["inventory"].pop(item["id"])
    refund = max(1, int(item["price"]) // 2) * quantity; economy_add(a, refund); save_config()
    await ctx.reply(embed=economy_embed(f"Sold **{quantity} × {item['name']}** for **{refund:,}** coins."))


@bot.command(name="use")
@commands.guild_only()
@commands.check(economy_command_guard)
async def use_item(ctx, item_id: str):
    a = economy_account(ctx.guild.id, ctx.author.id); item = economy_item(refresh_shop_items(ctx.guild.id), item_id)
    owned = int(a["inventory"].get(item_id.lower(), 0))
    if not item or owned < 1: return await ctx.reply(embed=economy_embed("You don't own that item."))
    a["inventory"][item["id"]] = owned - 1
    if not a["inventory"][item["id"]]: a["inventory"].pop(item["id"])
    save_config(); await ctx.reply(embed=economy_embed(f"You used {item.get('emoji', '✨')} **{item['name']}**. {item.get('description', '')}"))


async def withdraw_item_autocomplete(interaction: discord.Interaction, current: str):
    if interaction.guild is None:
        return []
    account = economy_account(interaction.guild.id, interaction.user.id)
    shop_items = get_shop_items(interaction.guild.id)
    choices = []
    for item_id, quantity in account.get("inventory", {}).items():
        if int(quantity) <= 0:
            continue
        item = economy_item(shop_items, item_id)
        name = item.get("name", item_id) if item else item_id
        emoji = item.get("emoji", "📦") if item else "📦"
        if current.lower() in item_id.lower() or current.lower() in name.lower():
            choices.append(discord.app_commands.Choice(name=f"{emoji} {name} · {item_id}"[:100], value=item_id))
    return choices[:25]


@bot.tree.command(name="withdraw", description="Redeem one shop item from your inventory")
@discord.app_commands.describe(item_id="Choose an item you own to redeem")
@discord.app_commands.autocomplete(item_id=withdraw_item_autocomplete)
async def slash_withdraw(interaction: discord.Interaction, item_id: str):
    if interaction.guild is None:
        return await interaction.response.send_message("Use this in a server where Supreme Bot is installed.", ephemeral=True)
    if interaction.channel_id != ECONOMY_CHANNEL_ID:
        return await interaction.response.send_message(f"Economy commands are only available in <#{ECONOMY_CHANNEL_ID}>.", ephemeral=True)
    guild = interaction.guild
    member = interaction.user
    guild_id = str(guild.id)
    if str(member.id) in {str(user_id) for user_id in config.get("blacklists", {}).get(guild_id, [])}:
        return await interaction.response.send_message("You are blacklisted from using Supreme Bot commands in this server.", ephemeral=True)
    if config.get("disabled_guilds", {}).get(guild_id, False):
        return await interaction.response.send_message("Supreme Bot commands are currently disabled in this server.", ephemeral=True)
    triggered, removed = record_economy_command(guild.id, member.id)
    if triggered:
        await audit(guild, f"Economy spam protection reset wallet and bank for {member.id}; removed {removed:,} coins")
        return await interaction.response.send_message(embed=economy_embed(f"Spam protection triggered: 5 economy commands within 10 seconds reset your wallet and bank (**{removed:,}** coins removed)."), ephemeral=True)
    account = economy_account(guild.id, member.id)
    item = economy_item(refresh_shop_items(guild.id), item_id)
    resolved_id = item["id"] if item else item_id.strip().lower()
    owned = int(account["inventory"].get(resolved_id, 0))
    if owned < 1:
        return await interaction.response.send_message("You don't have that item in your inventory.", ephemeral=True)
    item_name = item.get("name", resolved_id) if item else resolved_id
    item_emoji = item.get("emoji", "✨") if item else "✨"
    item_description = item.get("description", "") if item else ""
    channel_name = f"redeem-{member.id}-{resolved_id}"[:95]
    existing = discord.utils.get(guild.text_channels, name=channel_name)
    if existing:
        return await interaction.response.send_message(f"You already have a ticket for this item: {existing.mention}", ephemeral=True)

    await interaction.response.defer(ephemeral=True, thinking=True)
    ticket_channel = None
    try:
        bot_member = guild.me or await guild.fetch_member(bot.user.id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True),
        }
        supervisor_role_id = guild_setting("supervisor_roles", guild.id)
        if supervisor_role_id:
            supervisor_role = guild.get_role(int(supervisor_role_id))
            if supervisor_role:
                overwrites[supervisor_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        staff_role = discord.utils.find(lambda role: "staff team" in role.name.lower(), guild.roles)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        for owner_id in config.get("extra_owners", {}).get(str(guild.id), []):
            trusted_owner = guild.get_member(int(owner_id))
            if trusted_owner:
                overwrites[trusted_owner] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        if OWNER_ID:
            trusted_owner = guild.get_member(OWNER_ID)
            if trusted_owner:
                overwrites[trusted_owner] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        category = discord.utils.get(guild.categories, name="Support Tickets")
        if not category:
            category = await guild.create_category("Support Tickets")
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Shop redemption: {item_name} | {member} ({member.id})",
        )

        welcome = discord.Embed(
            title=f"{EMOJIS['ticket']} Item Redemption",
            description=f"Hi {member.mention}! Staff will review your redemption request. Keep this ticket open until they have given you **{item_name}**.",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        apply_embed_theme(guild.id, welcome)
        await ticket_channel.send(embed=welcome, view=TicketCloseView(), allowed_mentions=discord.AllowedMentions(users=[member]))

        request_embed = discord.Embed(title="📌 Redemption to fulfill", color=discord.Color.gold())
        request_embed.add_field(name="Item", value=f"{item_emoji} **{item_name}** (`{resolved_id}`)", inline=False)
        request_embed.add_field(name="Requested by", value=f"{member.mention} · `{member.id}`", inline=False)
        if item_description:
            request_embed.add_field(name="Item details", value=item_description[:1024], inline=False)
        request_embed.set_footer(text="Give the item to the member, then close this ticket.")
        pinned_request = await ticket_channel.send(embed=request_embed, allowed_mentions=discord.AllowedMentions(users=[member]))
        await pinned_request.pin(reason=f"Shop item redemption requested by {member} ({member.id})")

        current_account = economy_account(guild.id, member.id)
        current_owned = int(current_account["inventory"].get(resolved_id, 0))
        if current_owned < 1:
            await ticket_channel.delete(reason="Redemption inventory changed before ticket completion")
            return await interaction.followup.send("Your inventory changed before the request completed. No item was redeemed; try again.", ephemeral=True)
        current_account["inventory"][resolved_id] = current_owned - 1
        if current_account["inventory"][resolved_id] <= 0:
            current_account["inventory"].pop(resolved_id)
        if not save_config():
            current_account["inventory"][resolved_id] = current_owned
            await ticket_channel.delete(reason="Could not persist redeemed inventory item")
            return await interaction.followup.send("I couldn't save the redemption. Your item is still in your inventory; please try again later.", ephemeral=True)
    except discord.Forbidden:
        if ticket_channel:
            try:
                await ticket_channel.delete(reason="Could not complete item redemption ticket")
            except discord.HTTPException:
                pass
        return await interaction.followup.send("I couldn't create and pin the request. Give Supreme Bot Manage Channels, Send Messages, Embed Links, Manage Messages, and View Channel permissions, then try again. Your item is still in your inventory.", ephemeral=True)
    except discord.HTTPException:
        if ticket_channel:
            try:
                await ticket_channel.delete(reason="Could not complete item redemption ticket")
            except discord.HTTPException:
                pass
        return await interaction.followup.send("Discord couldn't finish creating your redemption ticket. Your item is still in your inventory; please try again.", ephemeral=True)

    await audit(guild, f"Shop redemption ticket created for {member} ({member.id}): {item_name} [{resolved_id}] | {ticket_channel.name}")
    await interaction.followup.send(f"Your {item_emoji} **{item_name}** redemption ticket is ready: {ticket_channel.mention}", ephemeral=True)


@bot.command(name="coinflipbet")
@commands.guild_only()
@commands.check(economy_command_guard)
async def coinflipbet(ctx, choice: str, amount: int):
    a=economy_account(ctx.guild.id,ctx.author.id); choice=choice.lower()
    if choice not in {"heads","tails"} or not 1 <= amount <= min(a["balance"],100000): return await ctx.reply(embed=economy_embed("Use `coinflipbet heads|tails amount` and wager coins you have (up to 100,000)."))
    result=random.choice(["heads","tails"]); win=(result==choice); delta=amount if win else -amount; a["balance"]+=delta
    if win: a["stats"]["earned"]+=amount
    else: a["stats"]["spent"]+=amount
    save_config(); await ctx.reply(embed=economy_embed(f"The coin landed **{result}** — {'you win' if win else 'you lose'} **{amount:,}** coins!"))


@bot.command(name="slots")
@commands.guild_only()
@commands.check(economy_command_guard)
async def slots(ctx, amount: int):
    a=economy_account(ctx.guild.id,ctx.author.id)
    if not 1 <= amount <= min(a["balance"],50000): return await ctx.reply(embed=economy_embed("Wager 1–50,000 coins you have."))
    icons=["🍒","🍋","🔔","💎","👑"]; roll=[random.choice(icons) for _ in range(3)]
    multiplier=8 if len(set(roll))==1 else 2 if len(set(roll))==2 else 0; change=amount*multiplier-amount
    a["balance"]+=change
    (a["stats"].__setitem__("earned",a["stats"].get("earned",0)+change) if change>0 else a["stats"].__setitem__("spent",a["stats"].get("spent",0)-change))
    save_config(); await ctx.reply(embed=economy_embed(f"{' '.join(roll)}\n{'Jackpot!' if multiplier==8 else 'Nice!' if multiplier else 'No match'} Net: **{change:+,}** coins."))


@bot.command(name="dice")
@commands.guild_only()
@commands.check(economy_command_guard)
async def dice(ctx, guess: int, amount: int):
    a=economy_account(ctx.guild.id,ctx.author.id)
    if not 1 <= guess <= 6 or not 1 <= amount <= min(a["balance"],50000): return await ctx.reply(embed=economy_embed("Use `dice <1-6> <wager>` with a wager you have."))
    rolled=random.randint(1,6); change=amount*4 if rolled==guess else -amount; a["balance"]+=change
    a["stats"]["earned"]+=max(0,change); a["stats"]["spent"]+=max(0,-change); save_config()
    await ctx.reply(embed=economy_embed(f"You guessed **{guess}**; the die rolled **{rolled}**. Net: **{change:+,}** coins."))


@bot.command(name="roulette")
@commands.guild_only()
@commands.check(economy_command_guard)
async def roulette(ctx, choice: str, amount: int):
    a=economy_account(ctx.guild.id,ctx.author.id); choice=choice.lower(); result=random.randint(0,36)
    if not 1 <= amount <= min(a["balance"],50000): return await ctx.reply(embed=economy_embed("Wager 1–50,000 coins you have."))
    color="green" if result==0 else "red" if result%2 else "black"
    if choice not in {"red", "black", "green"} and not (choice.isdigit() and 0 <= int(choice) <= 36): return await ctx.reply(embed=economy_embed("Choose red, black, green, or a number from 0 to 36."))
    won=choice==color or (choice.isdigit() and int(choice)==result)
    change=(amount*35 if choice.isdigit() and won else amount*35 if choice=="green" and won else amount if won else -amount)
    a["balance"]+=change; a["stats"]["earned"]+=max(0,change); a["stats"]["spent"]+=max(0,-change); save_config()
    await ctx.reply(embed=economy_embed(f"Wheel: **{result} {color}**. Net: **{change:+,}** coins."))


@bot.command(name="lottery")
@commands.guild_only()
@commands.check(economy_command_guard)
async def lottery(ctx, amount: int = 100):
    a=economy_account(ctx.guild.id,ctx.author.id)
    if not 1<=amount<=min(a["balance"],100000): return await ctx.reply(embed=economy_embed("Ticket price must be 1–100,000 coins you have."))
    wait=economy_cooldown_remaining(a,"lottery",86400,ctx)
    if wait: return await ctx.reply(embed=economy_embed(f"Next lottery ticket available in **{wait // 3600}h**."))
    a["balance"]-=amount; a["stats"]["spent"]+=amount; economy_mark_cooldown(a,"lottery")
    if random.random()<.08:
        reward=amount*10; economy_add(a,reward); result=f"Jackpot! Your **{amount:,}** coin ticket paid **{reward:,}** coins."
    else: result=f"No win this time. Your **{amount:,}** coin ticket is used. Try again tomorrow."
    save_config(); await ctx.reply(embed=economy_embed(result))

@bot.command(name="scratch")
@commands.guild_only()
@commands.check(economy_command_guard)
async def scratch(ctx, amount: int = 50):
    a=economy_account(ctx.guild.id,ctx.author.id)
    if not 1<=amount<=min(a["balance"],50000): return await ctx.reply(embed=economy_embed("Scratch card price must be 1–50,000 coins you have."))
    wait=economy_cooldown_remaining(a,"scratch",30,ctx)
    if wait: return await ctx.reply(embed=economy_embed(f"Wait **{wait}s** before buying another scratch card."))
    a["balance"]-=amount; a["stats"]["spent"]+=amount; economy_mark_cooldown(a,"scratch")
    if random.random()<.45:
        reward=random.randint(amount*2,amount*5); economy_add(a,reward); result=f"🎉 Scratch win! You paid **{amount:,}** and won **{reward:,}** coins."
    else: result=f"No prize. Your scratch card cost **{amount:,}** coins."
    save_config(); await ctx.reply(embed=economy_embed(result))

@bot.command(name="quest")
@commands.guild_only()
@commands.check(economy_command_guard)
async def quest(ctx):
    a=economy_account(ctx.guild.id,ctx.author.id); wait=economy_cooldown_remaining(a,"quest",86400,ctx)
    if wait: return await ctx.reply(embed=economy_embed(f"Your next quest refreshes in **{wait // 3600}h**."))
    reward=random.randint(180,400); economy_add(a,reward); economy_mark_cooldown(a,"quest"); save_config()
    await ctx.reply(embed=economy_embed(f"Quest complete: **{random.choice(['help a neighbor','explore the plaza','deliver a mystery package','find a lucky charm'])}**. Reward: **{reward}** coins."))


@bot.command(name="quests")
@commands.guild_only()
@commands.check(economy_command_guard)
async def quests(ctx):
    await ctx.reply(embed=economy_embed("**Daily quests**\n• Complete `quest` once per day — earn 180–400 coins.\n• Claim `daily` and `weekly` for bonus rewards.\n• Try `fish`, `hunt`, `crime`, or `work` to earn more."))


@bot.command(name="achievements")
@commands.guild_only()
@commands.check(economy_command_guard)
async def achievements(ctx):
    a=economy_account(ctx.guild.id,ctx.author.id)
    badges=[]
    if a["stats"].get("earned",0)>=1000: badges.append("💰 Coin Collector")
    if sum(a["inventory"].values())>=5: badges.append("🎒 Collector")
    if a.get("daily_streak",0)>=7: badges.append("🔥 Week Streak")
    await ctx.reply(embed=economy_embed("\n".join(badges) if badges else "No badges yet. Earn coins, shop, and keep your daily streak going!"))


@bot.command(name="streak")
@commands.guild_only()
@commands.check(economy_command_guard)
async def streak(ctx, member: discord.Member = None):
    member=member or ctx.author; a=economy_account(ctx.guild.id,member.id)
    await ctx.reply(embed=economy_embed(f"**{member.display_name}** has a daily streak of **{a.get('daily_streak',0)}** days."))


@bot.command(name="gift")
@commands.guild_only()
@commands.check(economy_command_guard)
async def gift(ctx, member: discord.Member, amount: int):
    await pay.callback(ctx, member, amount)


@bot.command(name="workstats")
@commands.guild_only()
@commands.check(economy_command_guard)
async def workstats(ctx, member: discord.Member = None):
    member=member or ctx.author; a=economy_account(ctx.guild.id,member.id)
    await ctx.reply(embed=economy_embed(f"**{member.display_name}** lifetime coins earned: **{a['stats'].get('earned',0):,}** · spent: **{a['stats'].get('spent',0):,}** · net worth: **{a['balance']+a['bank']:,}**."))


@bot.command(name="setshopitem")
@commands.guild_only()
@commands.check(economy_command_guard)
async def setshopitem(ctx, item_id: str, price: int, emoji: str, *, name: str):
    if not await require_economy_admin(ctx): return
    items=refresh_shop_items(ctx.guild.id); item=economy_item(items,item_id)
    if not 1 <= price <= 1000000000 or len(name)>80: return await ctx.reply(embed=economy_embed("Use a price from 1 to 1,000,000,000 and a name up to 80 characters."))
    if item: item.update({"price":price,"emoji":emoji[:80],"name":name})
    elif len(items)<100: items.append({"id":item_id.lower(),"name":name,"price":price,"emoji":emoji[:80],"description":""})
    else: return await ctx.reply(embed=economy_embed("The shop is full (100 items)."))
    config.setdefault("shop_items",{})[str(ctx.guild.id)]=items; save_config()
    await ctx.reply(embed=economy_embed(f"Saved {emoji} **{name}** for **{price:,}** coins."))


@bot.command(name="delshopitem", aliases=["shopremove"])
@commands.guild_only()
@commands.check(economy_command_guard)
async def delshopitem(ctx, item_id: str):
    if not await require_economy_admin(ctx): return
    items=refresh_shop_items(ctx.guild.id); item=economy_item(items,item_id)
    if not item: return await ctx.reply(embed=economy_embed("Shop item not found."))
    items.remove(item); save_config(); await ctx.reply(embed=economy_embed(f"Removed **{item['name']}** from the shop."))


@bot.command(name="setitemprice")
@commands.guild_only()
@commands.check(economy_command_guard)
async def setitemprice(ctx, item_id: str, price: int):
    if not await require_economy_admin(ctx): return
    item=economy_item(refresh_shop_items(ctx.guild.id),item_id)
    if not item or not 1 <= price <= 1000000000: return await ctx.reply(embed=economy_embed("Item not found or price invalid."))
    item["price"]=price; save_config(); await ctx.reply(embed=economy_embed(f"Updated **{item['name']}** to **{price:,}** coins."))


@bot.command(name="setitememoji")
@commands.guild_only()
@commands.check(economy_command_guard)
async def setitememoji(ctx, item_id: str, emoji: str):
    if not await require_economy_admin(ctx): return
    item=economy_item(refresh_shop_items(ctx.guild.id),item_id)
    if not item: return await ctx.reply(embed=economy_embed("Shop item not found."))
    item["emoji"]=emoji[:80]; save_config(); await ctx.reply(embed=economy_embed(f"Updated emoji for **{item['name']}** to {emoji}."))


@bot.command(name="clearinventory")
@commands.guild_only()
@commands.check(economy_command_guard)
async def clearinventory(ctx, member: discord.Member):
    if not await require_economy_admin(ctx): return
    a=economy_account(ctx.guild.id,member.id); a["inventory"].clear(); save_config()
    await ctx.reply(embed=economy_embed(f"Cleared {member.mention}'s inventory."))


@bot.command(name="addbank")
@commands.guild_only()
@commands.check(economy_command_guard)
async def addbank(ctx, member: discord.Member, amount: int):
    if not await require_economy_admin(ctx): return
    if not 1<=amount<=1000000000: return await ctx.reply(embed=economy_embed("Amount must be 1–1,000,000,000."))
    a=economy_account(ctx.guild.id,member.id); a["bank"]+=amount; save_config(); await ctx.reply(embed=economy_embed(f"Added **{amount:,}** coins to {member.mention}'s bank."))


@bot.command(name="removebank")
@commands.guild_only()
@commands.check(economy_command_guard)
async def removebank(ctx, member: discord.Member, amount: int):
    if not await require_economy_admin(ctx): return
    if not 1<=amount<=1000000000: return await ctx.reply(embed=economy_embed("Amount must be 1–1,000,000,000."))
    a=economy_account(ctx.guild.id,member.id); removed=min(amount,a["bank"]); a["bank"]-=removed; save_config(); await ctx.reply(embed=economy_embed(f"Removed **{removed:,}** coins from {member.mention}'s bank."))


@bot.command(name="resetbank")
@commands.guild_only()
@commands.check(economy_command_guard)
async def resetbank(ctx, member: discord.Member = None):
    if not await require_economy_admin(ctx): return
    accounts=config.setdefault("economy",{}).setdefault(str(ctx.guild.id),{})
    if member: economy_account(ctx.guild.id,member.id)["bank"]=0; text=f"Reset {member.mention}'s bank."
    else:
        for user_id in list(accounts): economy_account(ctx.guild.id,user_id)["bank"]=0
        text="Reset every bank in this server."
    save_config(); await ctx.reply(embed=economy_embed(text))


@bot.command(name="setdaily")
@commands.guild_only()
@commands.check(economy_command_guard)
async def setdaily(ctx, minimum: int, maximum: int):
    if not await require_economy_admin(ctx): return
    if not 0<=minimum<=maximum<=1000000: return await ctx.reply(embed=economy_embed("Use values from 0 to 1,000,000 with minimum ≤ maximum."))
    settings=get_economy_settings(ctx.guild.id); settings.update({"daily_min":minimum,"daily_max":maximum}); config.setdefault("economy_settings",{})[str(ctx.guild.id)]=settings; save_config()
    await ctx.reply(embed=economy_embed(f"Daily reward range set to **{minimum:,}–{maximum:,}** coins."))


@bot.command(name="setwork")
@commands.guild_only()
@commands.check(economy_command_guard)
async def setwork(ctx, minimum: int, maximum: int):
    if not await require_economy_admin(ctx): return
    if not 0<=minimum<=maximum<=1000000: return await ctx.reply(embed=economy_embed("Use values from 0 to 1,000,000 with minimum ≤ maximum."))
    settings=get_economy_settings(ctx.guild.id); settings.update({"work_min":minimum,"work_max":maximum}); config.setdefault("economy_settings",{})[str(ctx.guild.id)]=settings; save_config()
    await ctx.reply(embed=economy_embed(f"Work reward range set to **{minimum:,}–{maximum:,}** coins."))


@bot.command(name="setworkcooldown")
@commands.guild_only()
@commands.check(economy_command_guard)
async def setworkcooldown(ctx, seconds: int):
    if not await require_economy_admin(ctx): return
    if not 10<=seconds<=86400: return await ctx.reply(embed=economy_embed("Cooldown must be between 10 and 86,400 seconds."))
    settings=get_economy_settings(ctx.guild.id); settings["work_cooldown"]=seconds; config.setdefault("economy_settings",{})[str(ctx.guild.id)]=settings; save_config()
    await ctx.reply(embed=economy_embed(f"Work cooldown set to **{seconds} seconds**."))


@bot.command(name="shopclear")
@commands.guild_only()
@commands.check(economy_command_guard)
async def shopclear(ctx):
    if not await require_economy_admin(ctx): return
    config.setdefault("shop_items",{})[str(ctx.guild.id)]=[]; save_config()
    await ctx.reply(embed=economy_embed("Cleared the server shop."))


@bot.command(name="iteminfo")
@commands.guild_only()
@commands.check(economy_command_guard)
async def iteminfo(ctx, item_id: str):
    item=economy_item(refresh_shop_items(ctx.guild.id),item_id)
    if not item: return await ctx.reply(embed=economy_embed("Shop item not found."))
    embed=discord.Embed(title=f"{item.get('emoji','🛍️')} {item['name']}",description=item.get('description') or "No description.",color=discord.Color.blurple())
    embed.add_field(name="Item ID",value=f"`{item['id']}`"); embed.add_field(name="Price",value=f"{int(item['price']):,} coins")
    await ctx.reply(embed=embed)

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

import os
import aiohttp
import asyncio
import time
import discord

# =========================
# HUGGING FACE AI CONFIG
# =========================

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "").strip()
# Using a powerful, free-tier accessible instruction model via Hugging Face router
HF_MODEL = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.3-70B-Instruct").strip()
AI_HISTORY = {}
AI_LAST_REQUEST = {}

async def call_ai(guild_id, user_id, prompt):
    """Send a conversation request to Hugging Face's serverless Inference API."""
    if not HF_API_KEY:
        raise RuntimeError("AI is not configured yet. Set HUGGINGFACE_API_KEY in the hosting environment.")
    
    history_key = (int(guild_id), int(user_id))
    history = AI_HISTORY.get(history_key, [])[-6:]  # Keep last 6 turns for context
    
    # Format messages for Llama/OpenAI-compatible chat completions endpoint on Hugging Face
    messages = [
        {"role": "system", "content": "You are Supreme Bot AI, a friendly, helpful AI assistant chatting in a Discord server. Keep responses structured, concise, and easy to read. Use code blocks for code snippets."}
    ]
    for turn in history:
        messages.append(turn)
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": HF_MODEL,
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status >= 400:
                body = await response.text()
                if response.status == 401:
                    raise RuntimeError("The Hugging Face token was rejected. Check your HUGGINGFACE_API_KEY secret.")
                if response.status == 429:
                    raise RuntimeError("The Hugging Face rate limit was reached or model is loading. Try again shortly.")
                raise RuntimeError("The AI service returned an error. Try again later.")
            
            data = await response.json()

    try:
        answer = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise RuntimeError("The AI returned an unexpected response format. Please try again.")

    if not answer:
        raise RuntimeError("The AI returned an empty reply. Please try again.")

    # Update history
    AI_HISTORY[history_key] = history + [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": answer}
    ]
    
    return answer

# =========================
# COMMANDS
# =========================

@bot.command(name="ask", aliases=["ai", "chat"])
@commands.guild_only()
async def ask_ai(ctx, *, prompt: str):
    """Chat with Supreme Bot AI using Hugging Face."""
    prompt = prompt.strip()
    if not prompt:
        return await ctx.reply("Ask me something after the command, for example: `>ask explain how a computer works`", mention_author=False)
    if len(prompt) > 2000:
        return await ctx.reply("Please keep each message under 2,000 characters.", mention_author=False)
    
    key = (ctx.guild.id, ctx.author.id)
    now = time.monotonic()
    wait = 4 - (now - AI_LAST_REQUEST.get(key, 0))
    if wait > 0:
        return await ctx.reply(f"Give me {wait:.1f} seconds before your next AI message.", mention_author=False)
    AI_LAST_REQUEST[key] = now

    async with ctx.typing():
        try:
            answer = await call_ai(ctx.guild.id, ctx.author.id, prompt)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return await ctx.reply("I couldn't reach the Hugging Face AI service. Try again in a moment.", mention_author=False)
        except RuntimeError as exc:
            return await ctx.reply(str(exc), mention_author=False)

    # Chunk long responses to fit Discord's 2,000 character limit
    for start in range(0, len(answer), 1900):
        await ctx.reply(answer[start:start + 1900], mention_author=False, allowed_mentions=discord.AllowedMentions.none())


@bot.command(name="clearai", aliases=["resetai"])
@commands.guild_only()
async def clear_ai_history(ctx):
    """Clear your Hugging Face AI conversation memory in this server."""
    AI_HISTORY.pop((ctx.guild.id, ctx.author.id), None)
    await ctx.reply("Your AI chat history has been cleared.", mention_author=False)
    
@bot.command(name="help")
async def help_command(ctx):
    prefix = get_server_prefix(ctx.guild.id if ctx.guild else None)
    embed = discord.Embed(title=f"{EMOJIS['gear']} Supreme • Command Center", description=f"Full command list • Prefix varies by server. Economy commands only work in <#{ECONOMY_CHANNEL_ID}>.", color=discord.Color.blurple())
    embed.add_field(name=f"{EMOJIS['money']} Economy · Wallet & rewards", value=f"`{prefix}balance [@member]`, `{prefix}bank [@member]`, `{prefix}deposit <amount|all>`, `{prefix}withdraw <amount|all>`, `{prefix}daily`, `{prefix}weekly`, `{prefix}monthly`, `{prefix}work`, `{prefix}beg`, `{prefix}fish`, `{prefix}hunt`, `{prefix}crime`, `{prefix}rob @member`, `{prefix}pay @member amount`, `{prefix}gift @member amount`, `{prefix}leaderboard`, `{prefix}profile [@member]`, `{prefix}streak [@member]`, `{prefix}workstats [@member]`", inline=False)
    embed.add_field(name=f"{EMOJIS['success']} Economy · Games & goals", value=f"`{prefix}coinflipbet <heads|tails> amount`, `{prefix}slots amount`, `{prefix}dice <1-6> amount`, `{prefix}roulette <red|black|green|0-36> amount`, `{prefix}lottery [ticket-price]`, `{prefix}scratch [ticket-price]`, `{prefix}quest`, `{prefix}quests`, `{prefix}achievements`", inline=False)
    embed.add_field(name="🛍️ Economy · Shop", value=f"`{prefix}shop`, `{prefix}buy <item-id> [quantity]` adds items to your inventory, `{prefix}sell <item-id> [quantity]`, `{prefix}inventory [@member]`, `{prefix}use <item-id>`, `/withdraw` opens a private, pinned fulfillment ticket for one owned item, `{prefix}iteminfo <item-id>`", inline=False)
    embed.add_field(name=f"{EMOJIS['shield']} Economy · Manager tools", value=f"`{prefix}addmoney @member|all amount`, `{prefix}removemoney @member amount`, `{prefix}setmoney @member amount`, `{prefix}resetmoney [@member]`, `{prefix}reseteconomy all`, `{prefix}nocooldown @member`, `{prefix}removenocooldown @member`, `{prefix}addbank @member amount`, `{prefix}removebank @member amount`, `{prefix}resetbank [@member]`, `{prefix}setdaily min max`, `{prefix}setwork min max`, `{prefix}setworkcooldown seconds`, `{prefix}setshopitem id price emoji name`, `{prefix}delshopitem id`, `{prefix}setitemprice id price`, `{prefix}setitememoji id emoji`, `{prefix}clearinventory @member`, `{prefix}shopclear`", inline=False)
    embed.add_field(name=f"{EMOJIS['shield']} Staff & Moderation", value=f"`{prefix}promo`, `{prefix}demo`, `{prefix}super`, `{prefix}superintro`, `{prefix}staffintro`, `{prefix}staff`, `{prefix}role`, `{prefix}steal`, `{prefix}kick`, `{prefix}ban`, `{prefix}clear`, `{prefix}mute`", inline=False)
    embed.add_field(name=f"{EMOJIS['ticket']} Setup & Utility", value=f"`{prefix}dashboard`, `{prefix}ticketsetup`, `{prefix}ranks add @role`, `{prefix}ranks clear`, `{prefix}setstaffsupervisor`, `{prefix}setpromodemo`, `{prefix}setaudit`, `{prefix}staffsettings`, `{prefix}addextraowner @member`, `{prefix}removextraowner @member`, `{prefix}setactivity <type> <text>`, `{prefix}ping`, `{prefix}serverinfo`, `{prefix}userinfo`, `{prefix}avatar`, `{prefix}coinflip`, `{prefix}roll`", inline=False)
    embed.add_field(name="🤖 AI Chat & Tasks", value=f"Chat normally in the channel set with `{prefix}setaichannel #channel`; `{prefix}setaichannel off` disables it. Also: `{prefix}ask <message>` (aliases: `{prefix}ai`, `{prefix}chat`), `{prefix}clearai`, `{prefix}task <description>`, `{prefix}assign @member <task>` (supervisors), `{prefix}tasks [@member]`, `{prefix}done <task-id>`", inline=False)
    embed.add_field(name="🛡️ Server & Bot Controls", value=f"`{prefix}blacklist @member [reason]`, `{prefix}unblacklist @member`, `{prefix}disable`, `{prefix}enable`, `{prefix}shutdown`, `{prefix}restart`", inline=False)
    await ctx.reply(embed=embed, mention_author=False)


@bot.command(name="blacklist")
@commands.guild_only()
async def blacklist_member(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    """Block a member from using Supreme Bot commands in this server."""
    if not user_is_supervisor(ctx):
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only server owners, extra owners, or supervisors can blacklist members.", color=discord.Color.red()))
    protected_ids = {str(ctx.guild.owner_id), str(OWNER_ID)}
    protected_ids.update(str(uid) for uid in config.get("extra_owners", {}).get(str(ctx.guild.id), []))
    if str(member.id) in protected_ids:
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Bot owners and trusted owners cannot be blacklisted.", color=discord.Color.orange()))
    if member.bot:
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Bots cannot be blacklisted.", color=discord.Color.orange()))
    denied = config.setdefault("blacklists", {}).setdefault(str(ctx.guild.id), [])
    if str(member.id) in {str(uid) for uid in denied}:
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} {member.mention} is already blacklisted.", color=discord.Color.orange()))
    denied.append(str(member.id))
    if not save_config():
        denied.remove(str(member.id))
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Could not save the blacklist. Try again.", color=discord.Color.red()))
    reason = reason[:300]
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} {member.mention} is now blocked from using Supreme Bot commands in this server. Reason: {reason}", color=discord.Color.green()))


@bot.command(name="unblacklist", aliases=["pardon"])
@commands.guild_only()
async def unblacklist_member(ctx, member: discord.Member):
    """Restore a member's access to Supreme Bot commands in this server."""
    if not user_is_supervisor(ctx):
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only server owners, extra owners, or supervisors can remove a blacklist.", color=discord.Color.red()))
    guild_id = str(ctx.guild.id)
    denied = config.setdefault("blacklists", {}).setdefault(guild_id, [])
    if str(member.id) not in {str(uid) for uid in denied}:
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} {member.mention} is not blacklisted.", color=discord.Color.orange()))
    previous = list(denied)
    config["blacklists"][guild_id] = [str(uid) for uid in denied if str(uid) != str(member.id)]
    if not save_config():
        config["blacklists"][guild_id] = previous
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Could not save the blacklist change. Try again.", color=discord.Color.red()))
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} {member.mention} can use Supreme Bot commands again.", color=discord.Color.green()))


@bot.command(name="disable")
@commands.guild_only()
async def disable_bot(ctx):
    """Disable regular bot commands in this server."""
    if not user_is_owner(ctx):
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner, server owner, or extra owners can disable the bot here.", color=discord.Color.red()))
    guild_id = str(ctx.guild.id)
    previous = config.setdefault("disabled_guilds", {}).get(guild_id)
    config["disabled_guilds"][guild_id] = True
    if not save_config():
        if previous is None:
            config["disabled_guilds"].pop(guild_id, None)
        else:
            config["disabled_guilds"][guild_id] = previous
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Could not save this setting. Try again.", color=discord.Color.red()))
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Regular commands are disabled for this server. Use `{get_server_prefix(ctx.guild.id)}enable` to turn them back on.", color=discord.Color.orange()))


@bot.command(name="enable")
@commands.guild_only()
async def enable_bot(ctx):
    """Enable bot commands in this server."""
    if not user_is_owner(ctx):
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the bot owner, server owner, or extra owners can enable the bot here.", color=discord.Color.red()))
    guild_id = str(ctx.guild.id)
    previous = config.setdefault("disabled_guilds", {}).pop(guild_id, None)
    if not save_config():
        if previous is not None:
            config["disabled_guilds"][guild_id] = previous
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Could not save this setting. Try again.", color=discord.Color.red()))
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Bot commands are enabled again in this server.", color=discord.Color.green()))


@bot.command(name="shutdown")
async def shutdown_bot(ctx):
    """Stop the bot process. Bot owner only."""
    if not OWNER_ID or ctx.author.id != OWNER_ID:
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the configured bot owner can shut down the bot.", color=discord.Color.red()))
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Supreme Bot is shutting down.", color=discord.Color.orange()))
    await bot.close()


@bot.command(name="restart")
async def restart_bot(ctx):
    """Restart the bot process. Bot owner only."""
    if not OWNER_ID or ctx.author.id != OWNER_ID:
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} Only the configured bot owner can restart the bot.", color=discord.Color.red()))
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Supreme Bot is restarting.", color=discord.Color.green()))
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

@bot.command(name="dashboard")
async def dashboard(ctx):
    """Send the Supreme Bot dashboard link."""
    embed = discord.Embed(
        title="Supreme Bot Dashboard",
        url=DASHBOARD_URL,
        description=f"Open the [dashboard]({DASHBOARD_URL}) to manage your server settings, ticket panel, embeds, and economy.",
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Sign in with Discord to continue")
    await ctx.reply(embed=embed, mention_author=False, allowed_mentions=discord.AllowedMentions.none())

# =========================
# GAY LIST COMMANDS
# =========================

def get_gay_list(guild_id):
    """Retrieves or initializes the gay list for a specific guild."""
    if "gay_list" not in config:
        config["gay_list"] = {}
    return config["gay_list"].setdefault(str(guild_id), [])

@bot.command(name="gay")
@commands.guild_only()
async def gay_list_cmd(ctx):
    """Shows the list of added members."""
    guild_id = str(ctx.guild.id)
    members_list = get_gay_list(guild_id)
    
    if not members_list:
        await ctx.reply(embed=discord.Embed(description="🏳️‍🌈 The list is currently empty. Use `>addgay @member` to add someone.", color=discord.Color.blurple()))
        return
        
    mentions = [f"<@&{uid}>" if not str(uid).isdigit() else f"<@{uid}>" for uid in members_list]
    # Let's ensure they are formatted nicely as member mentions:
    formatted_mentions = []
    for uid in members_list:
        member = ctx.guild.get_member(int(uid))
        formatted_mentions.append(member.mention if member else f"`ID: {uid}`")

    embed = discord.Embed(
        title="🏳️‍🌈 Gay List (also known as bart list)",
        description="\n".join(formatted_mentions),
        color=discord.Color.magenta(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    await ctx.reply(embed=embed, mention_author=False)

@bot.command(name="addgay")
@commands.guild_only()
async def add_gay_cmd(ctx, member: discord.Member):
    """Adds a member to the list (Supervisor/Owner only)."""
    if not user_is_supervisor(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    guild_id = str(ctx.guild.id)
    members_list = get_gay_list(guild_id)
    
    if str(member.id) in members_list:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} {member.mention} is already on the list!", color=discord.Color.orange()))
        return

    members_list.append(str(member.id))
    save_config()
    
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Added {member.mention} to the list!", color=discord.Color.green()))
    await audit(ctx.guild, f"Member {member} ({member.id}) added to gay list by {ctx.author}")

@bot.command(name="removegay")
@commands.guild_only()
async def remove_gay_cmd(ctx, member: discord.Member):
    """Removes a member from the list (Supervisor/Owner only)."""
    if not user_is_supervisor(ctx):
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You don't have permission to use this command.", color=discord.Color.red()))
        return

    guild_id = str(ctx.guild.id)
    members_list = get_gay_list(guild_id)
    
    if str(member.id) not in members_list:
        await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} {member.mention} is not on the list.", color=discord.Color.orange()))
        return

    members_list.remove(str(member.id))
    save_config()
    
    await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['success']} Removed {member.mention} from the list.", color=discord.Color.green()))
    await audit(ctx.guild, f"Member {member} ({member.id}) removed from gay list by {ctx.author}")

# =========================
# CHECKGAY COMMAND
# =========================

@bot.command(name="checkgay")
@commands.guild_only()
async def checkgay(ctx, member: discord.Member = None):
    """Checks a member's percentage (0% for the bot owner)."""
    target = member or ctx.author
    
    # Check if the target is the bot owner
    if OWNER_ID and target.id == OWNER_ID:
        percentage = 0
        extra_text = " (ren has aura)"
    else:
        percentage = random.randint(0, 100)
        extra_text = ""

    embed = discord.Embed(
        title="🏳️‍🌈 Gay Rate Calculator",
        description=f"**{target.display_name}** is **{percentage}%** gay!{extra_text}",
        color=discord.Color.magenta(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    
    await ctx.reply(embed=embed, mention_author=False)

# =========================
# PRANK NUKE COMMAND
# =========================

@bot.command(name="nuke")
@commands.guild_only()
async def prank_nuke(ctx):
    """Sends a fake server nuke warning followed by a separate prank message."""
    
    # 1. Fake Initial Warning (Red Embed)
    fake_embed = discord.Embed(
        title="⚠️ SERVER NUKE INITIATED ⚠️",
        description=(
            "**WARNING:** A full server purge sequence has been triggered by "
            f"{ctx.author.mention}.\n\n"
            "```diff\n"
            "- Deleting all channels...\n"
            "- Purging member roles...\n"
            "- Wiping server configuration...\n"
            "```\n"
            "**Status:** `[████████████████----] 30%`\n"
            "*Executing final payload in 10 seconds...*"
        ),
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    apply_embed_theme(ctx.guild.id, fake_embed)
    
    # Send the scary message first
    await ctx.send(embed=fake_embed)
    
    # Wait 3 seconds for dramatic effect
    await asyncio.sleep(10)
    
    # 2. The Reveal (Green Embed sent as a NEW message)
    prank_embed = discord.Embed(
        title="🎉 GOTCHA! JUST A PRANK! 🎉",
        description=(
            f"Relax everyone! {ctx.author.mention} tried to nuke the server, "
            "but **Supreme Bot** protected everything! 🛡️\n\n"
            "✨ No channels, roles, or members were harmed."
        ),
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    apply_embed_theme(ctx.guild.id, prank_embed)
    
    # Send the prank reveal as its own separate message
    await ctx.send(embed=prank_embed)

# =========================
# EVENTS & STARTUP
# =========================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    ctx = await bot.get_context(message)
    guild = message.guild
    if guild is not None:
        ai_channel_id = config.get("ai_channels", {}).get(str(guild.id))
        is_blacklisted = str(message.author.id) in {str(uid) for uid in config.get("blacklists", {}).get(str(guild.id), [])}
        is_disabled = config.get("disabled_guilds", {}).get(str(guild.id), False)
        if (ai_channel_id and message.channel.id == int(ai_channel_id)
                and not ctx.valid and not is_blacklisted and not is_disabled
                and message.content.strip()):
            key = (guild.id, message.author.id)
            now = time.monotonic()
            wait = 5 - (now - AI_LAST_REQUEST.get(key, 0))
            if wait > 0:
                await message.reply(f"Give me {wait:.1f} seconds before your next AI message.", mention_author=False)
            else:
                AI_LAST_REQUEST[key] = now
                async with message.channel.typing():
                    try:
                        answer = await call_ai(guild.id, message.author.id, message.content[:2000])
                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        logging.exception("AI channel request failed")
                        answer = "I couldn't reach the AI service. Try again in a moment."
                    except RuntimeError as exc:
                        answer = str(exc)
                chunks = [answer[start:start + 1900] for start in range(0, len(answer), 1900)] or ["I couldn't create a reply."]
                await message.reply(chunks[0], mention_author=False, allowed_mentions=discord.AllowedMentions.none())
                for chunk in chunks[1:]:
                    await message.channel.send(chunk, allowed_mentions=discord.AllowedMentions.none())

    # Overriding on_message disables automatic command handling unless this is called.
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
            logging.info("Synced Supreme Bot slash commands")
        except discord.HTTPException:
            logging.exception("Could not sync slash commands; check that the app has the applications.commands scope")
    activity_settings = config.get("activity", {})
    if activity_settings.get("type") in ACTIVITY_TYPES and activity_settings.get("text"):
        await apply_bot_activity(activity_settings["type"], activity_settings["text"])
    logging.info("Supreme logged in as %s", bot.user)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, EconomySpamTriggered):
        return
    if isinstance(error, MemberBlacklisted):
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['error']} You are blacklisted from using Supreme Bot commands in this server.", color=discord.Color.red()))
    if isinstance(error, GuildCommandsDisabled):
        return await ctx.reply(embed=discord.Embed(description=f"{EMOJIS['warning']} Bot commands are disabled in this server.", color=discord.Color.orange()))
    if isinstance(error, EconomyChannelOnly):
        return await ctx.reply(embed=economy_embed(f"Economy commands are only available in <#{ECONOMY_CHANNEL_ID}>."))
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






















