from disco.bot import CommandLevels
from disco.voice.player import Player
from disco.voice.playable import YoutubeDLInput, BufferedOpusEncoderPlayable
from disco.voice.client import VoiceException
from disco.types.message import MessageTable

from rowboat.plugins import RowboatPlugin as Plugin, CommandFail, CommandSuccess
from rowboat.types import Field
from rowboat.models.guild import Guild
from rowboat.types.plugin import PluginConfig

class MusicConfig(PluginConfig):
    add_level = Field(int, default=10)
    skip_level = Field(int, default=10)

@Plugin.with_config(MusicConfig)
class MusicPlugin(Plugin):
    def load(self, ctx):
        super(MusicPlugin, self).load(ctx)
        self.guilds = {}

    @Plugin.command('join', group='music', level=CommandLevels.TRUSTED)
    def on_join(self, event):
        # g = Guild.select(Guild).where((Guild.guild_id == event.guild.id)).get()    

        # if g.premium == False and event.guild.id != '469566508838682644':
        #   raise CommandFail('This guild does not have premium enabled, please contact an Airplane global administrator.')

        if event.guild.id in self.guilds:
            return event.msg.reply("I'm already playing music here.")

        state = event.guild.get_member(event.author).get_voice_state()
        if not state:
            return event.msg.reply('You must be connected to voice to use that command.')

        try:
            client = state.channel.connect()
        except VoiceException as e:
            return event.msg.reply('Failed to connect to voice: `{}`'.format(e))

        self.guilds[event.guild.id] = Player(client)
        self.guilds[event.guild.id].complete.wait()
        del self.guilds[event.guild.id]

    def get_player(self, guild_id):
        if guild_id not in self.guilds:
            raise CommandFail("I'm not currently playing music here.")
        return self.guilds.get(guild_id)

    @Plugin.command('leave', group='music', level=CommandLevels.TRUSTED)
    def on_leave(self, event):
        self.get_player(event.guild.id).client.disconnect()

    @Plugin.command('play', '<url:str>', level=CommandLevels.TRUSTED)
    def on_play(self, event, url):
        # g = Guild.select(Guild).where((Guild.guild_id == event.guild.id)).get()
        
        # if g.premium == False and event.guild.id != '469566508838682644':
        #   raise CommandFail('This guild does not have premium enabled, please contact an Airplane global administrator.')
        
        item = YoutubeDLInput(url, command='ffmpeg').pipe(BufferedOpusEncoderPlayable)
        self.get_player(event.guild.id).queue.append(item)

    @Plugin.command('pause', level=CommandLevels.TRUSTED)
    def on_pause(self, event):
        self.get_player(event.guild.id).pause()

    @Plugin.command('resume', level=CommandLevels.TRUSTED)
    def on_resume(self, event):
        self.get_player(event.guild.id).resume()

    @Plugin.command('stop', level=CommandLevels.TRUSTED)
    def on_stop(self, event):
        self.get_player(event.guild.id).stop()

    @Plugin.command('kill', level=CommandLevels.MOD)
    def on_kill(self, event):
        self.get_player(event.guild.id).client.ws.sock.shutdown()

    @Plugin.command('queue', level=CommandLevels.TRUSTED)
    def on_queue(self, event):
        queue = self.get_player(event.guild.id).queue
        
        tbl = MessageTable()
        tbl.set_header('Title', 'Video Length', 'Author', 'Position', 'Added By')