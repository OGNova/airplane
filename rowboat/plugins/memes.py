from disco.bot import Plugin
from disco.bot import CommandLevels
from rowboat.types.plugin import PluginConfig

from disco.types.user import User as DiscoUser
from disco.types.message import MessageTable, MessageEmbed


class MemesConfig(PluginConfig):
    #auto-reply to meesux
    hate_mee6 = Field(bool, default=False)

@Plugin.with_config(MemesConfig)
class MemesPlugin(Plugin):
    def load(self, ctx):
        super(MemesPlugin, self).load(ctx)
    

    @Plugin.listen('MessageCreate')
    def meesucks_listener(self, event):
        if event.message.author.id != '159985870458322944':
            return
        event.message.reply('<@159985870458322944> **NO ONE CARES.**')

    @Plugin.listen('alexa play despacito')
    def alexa_play_despacito_listener(self, event):
        if event.message.author.id != '191793155685744640':
            return
        event.message.reply('des')
        gevent.sleep(.5)
        event.message.reply('pa')
        gevent.sleep(.5)
        event.message.reply('cito')