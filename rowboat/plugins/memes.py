import disco
import gevent
from rowboat.plugins import RowboatPlugin as Plugin, CommandFail, CommandSuccess
from disco.bot import CommandLevels
from rowboat.types.plugin import PluginConfig
from rowboat.redis import rdb
from disco.types.user import User as DiscoUser
from disco.types.message import MessageTable, MessageEmbed
from rowboat.types import Field, DictField, ListField, snowflake, SlottedModel, snowflake
from gevent.pool import Pool
from rowboat.util.gevent import wait_many


class MemesConfig(PluginConfig):
    #auto-reply to meesux
    hate_meesux = Field(bool, default=False)
@Plugin.with_config(MemesConfig)
class MemesPlugin(Plugin):
    def load(self, ctx):
        super(MemesPlugin, self).load(ctx)
    
    @Plugin.listen('MessageCreate')
    def alexa_play_despacito_listener(self, event):
        if "alexa play despacito" in event.content and event.author.id == 191793155685744640:
            def g():
                event.channel.send_message('des')
                gevent.sleep(.5)
                event.channel.send_message('pa')
                gevent.sleep(.5)
                event.channel.send_message('cito')
            gevent.spawn(g) 
    def meesucks_listener(self, event):
        if event.config.hate_meesux is False:
            return
        if event.author.id != 159985870458322944:
            return
        return event.channel.send_message('<@159985870458322944> **NO ONE CARES.**')

    @Plugin.command('pong', level=-1)
    def pong(self, event):
        return event.msg.reply('I pong, you ping. Idiot...')