import time
import gevent
import random
import weakref
import contextlib

from collections import deque
from holster.util import SimpleObject

from disco.bot import Plugin
from disco.gateway.packets import OPCode, RECV, SEND
from disco.util.snowflake import to_unix_ms


@contextlib.contextmanager
def timed():
    obj = SimpleObject()
    obj.start = time.time()
    yield obj
    obj.end = time.time()
    obj.duration = obj.end - obj.start


def generate_random_nonce(length=10):
    return random.randint(0, 2147483647)


class LatencyPlugin(Plugin):
    def load(self, ctx):
        super(LatencyPlugin, self).load(ctx)
        self.rtts = weakref.WeakValueDictionary()
        self.heartbeats = ctx.get('heartbeats') or deque(maxlen=100)
        self.last_heartbeat = None

    def unload(self, ctx):
        ctx['heartbeats'] = self.heartbeats
        super(LatencyPlugin, self).unload(ctx)

    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):
        if event.nonce in self.rtts:
            self.rtts[event.nonce].set()

    @Plugin.listen_packet((RECV, OPCode.HEARTBEAT_ACK))
    def on_heartbeat_ack(self, event):
        if self.last_heartbeat:
            self.heartbeats.append(int((time.time() - self.last_heartbeat) * 1000))

    @Plugin.listen_packet((SEND, OPCode.HEARTBEAT))
    def on_heartbeat(self, event):
        self.last_heartbeat = time.time()

    @Plugin.command('hb', group='latency')
    def hb(self, event):
        event.msg.reply('Last {} heartbeats:\n'.format(len(self.heartbeats)) +
            '  Average: `{}ms`\n'.format(sum(self.heartbeats) / len(self.heartbeats)) +
            '  Max: `{}ms`\n'.format(max(self.heartbeats)) +
            '  Min: `{}ms`\n'.format(min(self.heartbeats)))

    @Plugin.command('rtt')
    def rtt(self, event):
        """
        Measures the latency of sending a message and recieving it.
        """
        nonce = generate_random_nonce()
        self.rtts[nonce] = waiter = gevent.event.Event()

        with timed() as outer:
            with timed() as inner:
                msg = event.msg.reply('Latency Test', nonce=nonce)

            if not waiter.wait(timeout=15):
                event.msg.reply('I never recieved my latency test message!')
                return

        msg.edit(
            'RTT test complete\n' +
            '  Initial Send: `{}ms`\n'.format(int(inner.duration * 1000)) +
            '  Total RTT: `{}ms`\n'.format(int(outer.duration * 1000)) +
            '  Timestamp diff: `{}ms`\n'.format(int(inner.start * 1000) - to_unix_ms(msg.id))
            )