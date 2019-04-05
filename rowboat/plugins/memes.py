# -*- coding: utf-8 -*-
import disco
import gevent
import json
import requests

from random import randint, choice
from gevent.pool import Pool

from disco.bot import CommandLevels
from disco.types.user import User as DiscoUser
from disco.types.message import MessageTable, MessageEmbed

from rowboat.types import Field, DictField, ListField, snowflake, SlottedModel, snowflake
from rowboat.plugins import RowboatPlugin as Plugin, CommandFail, CommandSuccess
from rowboat.types.plugin import PluginConfig
from rowboat.redis import rdb
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
      
    @Plugin.command('smack', '<user:user|snowflake> [reason:str...]', level=-1)
    def smack(self, event, user, reason=None):
        return event.channel.send_message(u':clap: Smacked {User} (`{Reason}`)'.format(User=unicode(user), Reason=unicode(reason).encode('utf-8')))
   
    @Plugin.command('gay', '<user:user|snowflake>', aliases=['gey', 'ani'], level=-1)
    def gay(self, event, user):
        member = event.guild.get_member(user)
        return event.channel.send_message(u':rainbow: {Member}, ur gey'.format(Member=member.mention))

    @Plugin.command('hug', '<user:user|snowflake>', level=-1)
    def hug(self, event, user):
        member = event.guild.get_member(user)
        try:
            r = requests.get('https://nekos.life/api/v2/img/hug')
            url = r.text.split('"')[3]
        except:
            event.msg.reply('404 hug not found')
        
        r = requests.get(url, stream=True)

        event.msg.reply('{}'.format(member.mention), attachments=[('hug.gif', r.raw)])

    @Plugin.command('pat', '<user:user|snowflake>', level=-1)
    def pat(self, event, user):
        member = event.guild.get_member(user)
        try:
            r = requests.get('https://nekos.life/api/v2/img/pat')
            url = r.text.split('"')[3]
        except:
            event.msg.reply('404 pat not found')
        
        r = requests.get(url, stream=True)

        event.msg.reply('{}'.format(member.mention), attachments=[('pat.gif', r.raw)])

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

    @Plugin.command('rockpaperscissors', '[user:user|snowflake]', aliases = ['rps'], level=10)
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
                event.msg.reply('{}, you failed to make your choice.'.format(p_1[0].mention)).after(5).delete()
                return
            if mra_event.emoji.id == game_emotes_rps['rock']['default']['id']:
                p_1.append('rock')
            elif mra_event.emoji.id == game_emotes_rps['paper']['default']['id']:
                p_1.append('paper')
            elif mra_event.emoji.id == game_emotes_rps['scissors']['default']['id']:
                p_1.append('scissors')
            else:
                raise CommandFail('invalid emoji selected.')
            prompt.delete()
            rand_options = ['rock', 'paper', 'scissors']
            p_2.append(choice(rand_options))
            outcome = winner_rps(p_1[1], p_2[1])
            p_1.append(outcome[0])
            p_2.append(outcome[1])
            output = '**Results:**\n{0}: <:{2}> `{1}`\n{3}: <:{5}> `{4}`. \n' + outcome[2]
            event.msg.reply(output.format(p_1[0].mention, p_1[1], game_emotes_rps[p_1[1]][p_1[2]]['emote'], p_2[0].mention, p_2[1], game_emotes_rps[p_2[1]][p_2[2]]['emote']))
        
        else:
            p_2.append(event.guild.get_member(user))
            if p_1[0].id == p_2[0].id:
                event.msg.reply('You cannot play against yourself.').after(5).delete()
                return
            msg = event.msg.reply('{1}, {0} has challenged you to play rock paper scissors. Do you accept?'.format(p_1[0].mention, p_2[0].mention))
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
                    )).get(timeout=20)
            except gevent.Timeout:
                event.msg.reply('{}, your challenge timed out.'.format(p_1[0].mention)).after(5).delete()
                return
            finally:
                msg.delete()
    
            if str(mra_event.emoji.id) != str(GREEN_TICK_EMOJI_ID):
                event.msg.reply('{}, your partner has declined the challenge.'.format(p_1[0].mention)).after(5).delete()
                return
            else:
                try: # Send dm to the first user
                    prompt_p1 = p_1[0].open_dm().send_message('{}, Rock, Paper, Scissors says shoot! (Please react to one of the following).'.format(p_1[0].mention))
                except:
                    event.msg.reply('{0}, your DMs are disabled, therefore you are unable to challenge another user. Please open your DMs and try again.'.format(p_1[0].mention)).after(5).delete()
                    return
                temp = event.msg.reply('{} is selecting their choice, please wait.'.format(unicode(p_1[0].username)))
                prompt_p1.chain(False).\
                    add_reaction(game_emotes_rps['rock']['default']['emote']).\
                    add_reaction(game_emotes_rps['paper']['default']['emote']).\
                    add_reaction(game_emotes_rps['scissors']['default']['emote'])
                try:
                    mra_event = self.wait_for_event(
                        'MessageReactionAdd',
                        message_id = prompt_p1.id,
                        conditional = lambda e: (
                            e.emoji.id in (game_emotes_rps['rock']['default']['id'], game_emotes_rps['paper']['default']['id'], game_emotes_rps['scissors']['default']['id']) and
                            e.user_id == p_1[0].id
                        )).get(timeout=15)
                except gevent.Timeout:
                    prompt_p1.delete()
                    temp.delete()
                    event.msg.reply('Game canceled, {} failed to make their choice.'.format(p_1[0].mention)).after(5).delete()
                    return
                if mra_event.emoji.id == game_emotes_rps['rock']['default']['id']:
                    p_1.append('rock')
                elif mra_event.emoji.id == game_emotes_rps['paper']['default']['id']:
                    p_1.append('paper')
                elif mra_event.emoji.id == game_emotes_rps['scissors']['default']['id']:
                    p_1.append('scissors')
                temp.delete()
                prompt_p1.delete()
                try: # Send dm to second user
                    prompt_p2 = p_2[0].user.open_dm().send_message('{}, Rock, Paper, Scissors says shoot! (Please react to one of the following).'.format(p_2[0].mention))
                except:
                    event.msg.reply('{0}, your DMs are disabled, therefore you are unable play other users. Please open your DMs and try again.'.format(p_2[0].mention)).after(5).delete()
                    return
                temp = event.msg.reply('{} is selecting their choice, please wait.'.format(unicode(p_2[0].user.username)))
                prompt_p2.chain(False).\
                    add_reaction(game_emotes_rps['rock']['default']['emote']).\
                    add_reaction(game_emotes_rps['paper']['default']['emote']).\
                    add_reaction(game_emotes_rps['scissors']['default']['emote'])
                try:
                    mra_event = self.wait_for_event(
                        'MessageReactionAdd',
                        message_id = prompt_p2.id,
                        conditional = lambda e: (
                            e.emoji.id in (game_emotes_rps['rock']['default']['id'], game_emotes_rps['paper']['default']['id'], game_emotes_rps['scissors']['default']['id']) and
                            e.user_id == p_2[0].id
                        )).get(timeout=15)
                except gevent.Timeout:
                    prompt_p2.delete()
                    temp.delete()
                    event.msg.reply('Game canceled, {} failed to make their choice.'.format(p_2[0].mention)).after(5).delete()
                    return
                if mra_event.emoji.id == game_emotes_rps['rock']['default']['id']:
                    p_2.append('rock')
                elif mra_event.emoji.id == game_emotes_rps['paper']['default']['id']:
                    p_2.append('paper')
                elif mra_event.emoji.id == game_emotes_rps['scissors']['default']['id']:
                    p_2.append('scissors')
                prompt_p2.delete()
                temp.delete()
                outcome = winner_rps(p_1[1], p_2[1])
                p_1.append(outcome[0])
                p_2.append(outcome[1])
                output = '**Results:**\n{0}: <:{2}> `{1}`\n{3}: <:{5}> `{4}`. \n' + outcome[2]
                return event.msg.reply(output.format(p_1[0].mention, p_1[1], game_emotes_rps[p_1[1]][p_1[2]]['emote'], p_2[0].mention, p_2[1], game_emotes_rps[p_2[1]][p_2[2]]['emote']))               
        
