# -*- coding: utf-8 -*-
import disco
import gevent
import json
from random import randint, choice
from rowboat.plugins import RowboatPlugin as Plugin, CommandFail, CommandSuccess
from disco.bot import CommandLevels
from rowboat.types.plugin import PluginConfig
from rowboat.redis import rdb
from disco.types.user import User as DiscoUser
from disco.types.message import MessageTable, MessageEmbed
from rowboat.types import Field, DictField, ListField, snowflake, SlottedModel, snowflake
from gevent.pool import Pool
from rowboat.util.gevent import wait_many
from rowboat.constants import (
    GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID, GREEN_TICK_EMOJI, RED_TICK_EMOJI
)

game_emotes_rps = {
    "scissors": {
        "default": {
            "id": 550773044696580097,
            "emote": "choose_scissors:550773044696580097"
        },
        "won": {
            "id": 550773044906426378,
            "emote": "scissors_won:550773044906426378"
        },
        "lost": {
            "id": 550773044927397906,
            "emote": "scissors_lost:550773044927397906"
        }
    },
    "rock": {
        "default": {
            "id": 550773044855963677,
            "emote": "choose_rock:550773044855963677"
        },
        "won": {
            "id": 550773044923072512,
            "emote": "rock_won:550773044923072512"
        },
        "lost": {
            "id": 550773044914683907,
            "emote": "rock_lost:550773044914683907"
        }
    },
    "paper": {
        "default": {
            "id": 550773044277411852,
            "emote": "choose_paper:550773044277411852"
        },
        "won": {
            "id": 550773044738654208,
            "emote": "paper_won:550773044738654208"
        },
        "lost": {
            "id": 550773044881129486,
            "emote": "paper_lost:550773044881129486"
        }
    }
}

def winner_rps(choice_p1, choice_p2):
    if choice_p1 == choice_p2:
        outcome_p1 = 'default'
        outcome_p2 = 'default'
        return outcome_p1, outcome_p2, "{0} and {3} both chose {1} making this game a tie."
    elif choice_p1 == 'rock':
        if choice_p2 == 'paper':
            outcome_p1 = 'lost'
            outcome_p2 = 'won'
            return outcome_p1, outcome_p2, "{3} beat {0} by playing {4}."
        elif choice_p2 == 'scissors':
            outcome_p1 = 'won'
            outcome_p2 = 'lost'
            return outcome_p1, outcome_p2, "{0} beat {3} by playing {1}"
    elif choice_p1 == 'scissors':
        if choice_p2 == 'paper':
            outcome_p1 = 'won'
            outcome_p2 = 'lost'
            return outcome_p1, outcome_p2, "{0} beat {3} by playing {1}"
        elif choice_p2 == 'rock':
            outcome_p1 = 'lost'
            outcome_p2 = 'won'
            return outcome_p1, outcome_p2, "{3} beat {0} by playing {4}."
    elif choice_p1 == 'paper':
        if choice_p2 == 'scissors':
            outcome_p1 = 'lost'
            outcome_p2 = 'won'
            return outcome_p1, outcome_p2, "{3} beat {0} by playing {4}."
        elif choice_p2 == 'rock':
            outcome_p1 = 'won'
            outcome_p2 = 'lost'
            return outcome_p1, outcome_p2, "{0} beat {3} by playing {1}"

class MemesConfig(PluginConfig):
    #auto-reply to meesux
    hate_meesux = Field(bool, default=False)

@Plugin.with_config(MemesConfig)
class MemesPlugin(Plugin):
    def load(self, ctx):
        super(MemesPlugin, self).load(ctx)
    
    # @Plugin.listen('MessageCreate')
    # def alexa_play_despacito_listener(self, event):
    #     if "hey alexa" in event.content and event.author.id == 191793155685744640:
    #         msg = event.channel.send_message('<a:hey_alexa:473213508171989023>')
    #         try:
    #             alexa_event = self.wait_for_event(
    #                 'MessageCreate',
    #                 conditional=lambda e: (
    #                     e.author == event.author.id
    #                 )).get(timeout=10)

    #             # cancel
    #             if "cancel" in alexa_event.content.lower():
    #                 msg.delete()
    #                 return
    #             # despacito
    #             if "play despacito" in alexa_event.content.lower():
    #                 msg.delete()
    #                 event.channel.send_message('Ok, playing Despacito on <:spotify:473223054831517727>')
    #                 def g():
    #                     event.channel.send_message('des')
    #                     gevent.sleep(.5)
    #                     event.channel.send_message('pa')
    #                     gevent.sleep(.5)
    #                     event.channel.send_message('cito')
    #                 gevent.spawn(g)

    #             # Ligma LOL SO FUNNY HAHAHA
    #             if "what is ligma" in alexa_event.content.lower():
    #                 msg.delete()
    #                 event.channel.send_message('<@!' + alexa_event.author + '> your ignorance is amusing.')

    #             # sugma haha funny too
    #             if "what is sugma" in alexa_event.content.lower():
    #                 msg.delete()
    #                 def h():
    #                     new_msg = event.channel.send_message("Ok. Nope that's it. I'm done.")
    #                     gevent.sleep(2)
    #                     new_msg.edit('Shutting down...')
    #                     gevent.sleep(2.5)
    #                     new_msg.edit('Goodbye.')
    #                 gevent.spawn(h)

    #             # timer
    #             # if "set a timer for" in alexa_event.content.lower():
    #             #     msg.delete()

    #         except gevent.Timeout:
    #             msg.delete()
    #             return
            


    @Plugin.listen('MessageCreate')
    def meesucks_listener(self, event):
        if event.config.hate_meesux is True:
            if event.author.id == 159985870458322944:
                return event.channel.send_message('<@159985870458322944> **NO ONE CARES.**')

    @Plugin.command('pong', level=-1)
    def pong(self, event):
        return event.msg.reply('I pong, you ping. Idiot...')

    @Plugin.command('banana', '<user:user|snowflake> [reason:str...]', level=-1)
    def banana(self, event, user, reason=None):
        #Love my banana command, kthx ~Justin
        return event.channel.send_message(u':banana: Banana\'d {User} (`{Reason}`)'.format(User=unicode(user), Reason=unicode(reason).encode('utf-8')))

    @Plugin.command('kik', '<user:user|snowflake> [reason:str...]', level=-1)
    def kik(self, event, user, reason=None):
        #Kik'd
        return event.channel.send_message(u'<:kik:535264925237510194> Kik\'d {User} (`{Reason}`)'.format(User=unicode(user), Reason=unicode(reason).encode('utf-8')))

    @Plugin.command('bean', '<user:user|snowflake> [reason:str...]', level=-1)
    def bean(self, event, user, reason=None):
        #Bean'd
        return event.channel.send_message(u'<:beaned:321111606878797825> Bean\'d {User} (`{Reason}`)'.format(User=unicode(user), Reason=unicode(reason).encode('utf-8')))

    @Plugin.command('fight', '[user:user|snowflake]', level=10)
    def fight(self, event, user=None):
        with open('./fun.json') as f:
            fun = json.load(f)
        fights = fun["fights"]
        author = event.author.mention
        if not user or event.author.id == user.id:
            content = fights["id" == "0"]["content"]
            return event.msg.reply(content.format(author))
        else:
            target = user.mention
        content = fights[randint(1, len(fights)-1)]["content"]
        return event.msg.reply(content.format(target, author))

    @Plugin.command('rockpaperscissors', '[user:user|snowflake]', aliases = ['rps'], level=-1)
    def rps(self, event, user=None):
        p_1 = []
        p_1.append(event.author)
        p_2 = []
        
        if not user:
            p_2.append(event.guild.get_member(351097525928853506)) # Airplane :D
            prompt = event.msg.reply('{}, Rock, Paper, Scissors says shoot! (Please react to one of the following).'.format(p_1[0].mention))
            prompt.chain(False).\
                add_reaction(game_emotes_rps['rock']['default']['emote']).\
                add_reaction(game_emotes_rps['paper']['default']['emote']).\
                add_reaction(game_emotes_rps['scissors']['default']['emote'])
            try:
                mra_event = self.wait_for_event(
                    'MessageReactionAdd',
                    message_id = prompt.id,
                    conditional = lambda e: (
                        e.emoji.id in (game_emotes_rps['rock']['default']['id'], game_emotes_rps['paper']['default']['id'], game_emotes_rps['scissors']['default']['id']) and
                        e.user_id == event.author.id
                    )).get(timeout=15)
            except gevent.Timeout:
                prompt.delete()
                event.msg.reply('{}, you failed to make your choice.'.format(p_1[0].mention))
            if mra_event.emoji.id == game_emotes_rps['rock']['default']['id']:
                p_1.append('rock')
            elif mra_event.emoji.id == game_emotes_rps['paper']['default']['id']:
                p_1.append('paper')
            elif mra_event.emoji.id == game_emotes_rps['scissors']['default']['id']:
                p_1.append('scissors')
            else:
                raise CommandFail('invalid emoji selected.')
            rand_options = ['rock', 'paper', 'scissors']
            p_2.append(choice(rand_options))
            outcome = winner_rps(p_1[1], p_2[1])
            p_1.append(outcome[0])
            p_2.append(outcome[1])
            output = '**Results:**\n{0}: <:{2}> `{1}`\n{3}: <:{5}> `{4}`. \n' + outcome[2]
            event.msg.reply(output.format(p_1[0].mention, p_1[1], game_emotes_rps[p_1[1]][p_1[2]]['emote'], p_2[0].mention, p_2[1], game_emotes_rps[p_2[1]][p_2[2]]['emote']))
        
        else:
            p_2.append(event.guild.get_member(user))
            try:
                p_1[0].user.open_dm()
            except:
                event.msg.reply('{0}, your DMs are disabled, therefore you are unable to challenge another user. Please open your DMs and try again.'.format(p_1[0].mention))
            try:
                p_2[0].user.open_dm()
            except:
                event.msg.reply('{0}, this user is unable to play rock paper scissors as their DMs are disabled.'.format(p_1[0].mention))
            msg = event.msg.reply('{1}, {0} has challanged you to play rock paper scissors. Do you accept?'.format(p_1[0].mention, p_2[0].mention))
            msg.chain(False).\
                add_reaction(GREEN_TICK_EMOJI).\
                add_reaction(RED_TICK_EMOJI)
    
            try:
                mra_event = self.wait_for_event(
                    'MessageReactionAdd',
                    message_id=msg.id,
                    conditional=lambda e: (
                        e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                        e.user_id == p_2[0].id
                    )).get(timeout=30)
            except gevent.Timeout:
                msg.edit('Challenge timed out.').after(5).delete()
                return
            finally:
                msg.delete()
    
            if str(mra_event.emoji.id) != str(GREEN_TICK_EMOJI_ID):
                return
            else:
                event.msg.reply('yee').after(5).delete()
            