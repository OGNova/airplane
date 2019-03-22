import re
import yaml
from disco.types.user import GameType, Status

# Emojis
GREEN_TICK_EMOJI_ID = 470283598600208394
RED_TICK_EMOJI_ID = 470285164313051138
GREEN_TICK_EMOJI = 'approve:{}'.format(GREEN_TICK_EMOJI_ID)
RED_TICK_EMOJI = 'deny:{}'.format(RED_TICK_EMOJI_ID)
STAR_EMOJI = u'\U00002B50'
STATUS_EMOJI = {
    Status.ONLINE: ':status_online:351889710056210432',
    Status.IDLE: ':status_away:351889707681972234',
    Status.DND: ':status_dnd:351889706285400075',
    Status.OFFLINE: ':status_offline:351889709078937601',
    GameType.STREAMING: ':status_streaming:351889710253080587',
}
SNOOZE_EMOJI = u'\U0001f4a4'


# Regexes
INVITE_LINK_RE = re.compile(r'(discordapp.com/invite|discord.me|discord.gg)(?:/#)?(?:/invite)?/([a-z0-9\-]+)', re.I)
URL_RE = re.compile(r'(https?://[^\s]+)')
EMOJI_RE = re.compile(r'<a?:(.+):([0-9]+)>')
USER_MENTION_RE = re.compile('<@!?([0-9]+)>')

# IDs and such
ROWBOAT_GUILD_ID = 469566508838682644
ROWBOAT_USER_ROLE_ID = 469566789697667112
ROWBOAT_LAUNCH_CHANNEL = 469566915145105438
ROWBOAT_CONFIG_CHANNEL = 469567010523578368
ROWBOAT_ERROR_CHANNEL = 469566600425766913
ROWBOAT_JOIN_CHANNEL = 471058191585771568
ROWBOAT_LOG_CHANNEL = 497553178447839253

# Discord Error codes
ERR_UNKNOWN_MESSAGE = 10008

# Etc
YEAR_IN_SEC = 60 * 60 * 24 * 365
CDN_URL = 'https://twemoji.maxcdn.com/2/72x72/{}.png'

# Loaded from files
with open('data/badwords.txt', 'r') as f:
    BAD_WORDS = f.readlines()

# Merge in any overrides in the config
with open('config.yaml', 'r') as f:
    loaded = yaml.load(f.read())
    locals().update(loaded.get('constants', {}))
