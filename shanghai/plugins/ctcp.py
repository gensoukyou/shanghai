
import functools

from shanghai.event import (
    Priority, MessageEventDispatcher, core_message_event,
    core_network_event, NetworkEventName
)
from shanghai.irc import Message
from shanghai.network import NetworkContext

__plugin_name__ = 'CTCP'
__plugin_version__ = '0.0.2'
__plugin_description__ = 'CTCP Message processing'


class CtcpMessage(Message):

    def __repr__(self):
        return '<CTCP command={!r} params={!r}>'.format(self.command, self.params)

    @classmethod
    def from_message(cls, msg: Message):
        """Very primitive but should do the job for now."""
        if not msg.command == 'PRIVMSG':
            return None
        line = msg.params[1]
        if not line.startswith('\x01') or not line.endswith('\x01'):
            return None
        line = line[1:-1].rstrip()
        if not line:
            return None
        ctcp_cmd, *ctcp_params = line.split(' ', 1)
        if not ctcp_cmd:
            return None
        ctcp_cmd = ctcp_cmd.upper()
        if ctcp_params:
            ctcp_params = ctcp_params[0].split()
        return cls(ctcp_cmd, prefix=msg.prefix, params=ctcp_params)


def send_ctcp(ctx: NetworkContext, target: str, command: str, text: str = None):
    if text:
        text = ' ' + text
    text = '\x01{}{}\x01'.format(command, text)
    return ctx.send_msg(target, text)


def send_ctcp_reply(ctx: NetworkContext, target: str, command: str, text: str = None):
    if text:
        text = ' ' + text
    text = '\x01{}{}\x01'.format(command, text)
    return ctx.send_notice(target, text)


@core_network_event(NetworkEventName.INIT_CONTEXT)
async def init_context(ctx: NetworkContext, _):
    NetworkContext.add_cls_method('send_ctcp', send_ctcp)
    NetworkContext.add_cls_method('send_ctcp_reply', send_ctcp_reply)


# provide an event dispatcher for CTCP events
ctcp_event_dispatcher = MessageEventDispatcher()


# decorator
def ctcp_event(name, priority=Priority.DEFAULT):
    dispatcher = ctcp_event_dispatcher

    def deco(coroutine):
        dispatcher.register(name, coroutine, priority)
        coroutine.unregister = functools.partial(dispatcher.unregister, name, coroutine)
        return coroutine

    return deco


@core_message_event('PRIVMSG')
async def privmsg(ctx: NetworkContext, msg: Message):
    ctcp_msg = CtcpMessage.from_message(msg)
    if ctcp_msg:
        await ctcp_event_dispatcher.dispatch(ctx, ctcp_msg)


# example ctcp_event hook
@ctcp_event('VERSION')
async def version_request(ctx: NetworkContext, msg: CtcpMessage):
    source = msg.prefix[0]
    ctx.send_ctcp_reply(source, 'VERSION', 'Shanghai v37')
