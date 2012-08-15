# lambdairc.py: a Python IRC library full of lambdas and braces
# Author: mcef@discordiae.com
# License: GNU GPL v2 or later <https://www.gnu.org/licenses/gpl-2.0.html>
# Length: 3 logical lines of code

user = type( # represents IRC user; constructed from source part of raw message (if only one param), otherwise from str, bool, str, str
    'user',
    (object,),
    {
        '__init__': lambda self, nick, tilde=None, username=None, host=None: ( # if only nick is given, it's parsed into the rest
            (lambda m: (
                (
                    setattr(self, 'nick', m.group(1)),
                    setattr(self, 'tilde', bool(m.group(2))),
                    setattr(self, 'username', m.group(3)),
                    setattr(self, 'host', m.group(4)),
                ) if m else setattr(self, 'nick', None),
            ))(self.user_re.match(nick)) if tilde is None and username is None and host is None else (
                setattr(self, 'nick', nick),
                setattr(self, 'tilde', bool(tilde)),
                setattr(self, 'username', username),
                setattr(self, 'host', host),
            ),
            None,
        )[-1],
        '__str__': lambda self: ( # formats back to source-syntax
            ('%s!%s@%s' % (self.nick, '~'+self.username if self.tilde else self.username, self.host)) if self.nick is not None else ''
        ),
        'user_re': (lambda re: (
            re.compile('^([^\\s]+)!(~?)([^\\s]+)@([^\\s]+)$') # nick!~username@host or nick!username@host
        ))(__import__('re')),
    }
)

message = type( # an IRC message; constructed from raw message (if only one param), otherwise from str, str, list of str, str (any but cmd can be None)
    'message',
    (object,),
    {
        '__init__': lambda self, source, cmd=None, params=None, msg=None: ( # if only source is given, a raw message is parsed
            self.parse(source) if cmd is None and params is None and msg is None else self.construct(source, cmd, params, msg),
            None,
        )[-1],
        '__str__': lambda self: ( # returns a raw IRC message, including CRLF, or '' if this message instance is invalid
            '' if self.invalid else ' '.join(i for i in (
                ':' + self.source if self.source else None,
                self.cmd.upper(),
                ' '.join(self.params) if self.params else None,
                ':' + self.msg if self.msg else None,
            ) if i) + '\r\n'
        ),
        '__repr__': lambda self: ( # returns a raw IRC message, including CRLF, or '' if this message instance is invalid
            repr(str(self))
        ),
        'invalid': (False), # True if there was some error
        'parse': lambda self, raw: (# parses a raw message
            (lambda m: (
                (
                    setattr(self, 'source', m.group(1).strip() if m.group(1) else None),
                    (
                        setattr(self, 'user', user(self.source)),
                        setattr(self, 'user', None) if self.user.nick is None else None,
                    ) if self.source is not None else setattr(self, 'user', None),
                    setattr(self, 'cmd', m.group(2).strip().upper()),
                    setattr(self, 'params', [p.strip() for p in self.param_re.findall(m.group(3))] if m.group(3) else None),
                    setattr(self, 'msg', m.group(4).strip() if m.group(4) else None),
                ) if m else setattr(self, 'invalid', True)
            ))(self.msg_re.match(raw))
        ),
        'msg_re': (lambda re: ( # matches an IRC message
            re.compile('^(?:[:@]([^\\s]+) )?([^\\s]+)(?: ((?:[^:\\s][^\\s]* ?)*))?(?: ?:(.*))?(\\r\\n)?$')
        ))(__import__('re')),
        'param_re': (lambda re: ( # matches a IRC command parameter
            re.compile('(?:[^:\\s][^\\s]* ?)')
        ))(__import__('re')),
        'construct': lambda self, source, cmd, params, msg: ( # constructs the message from parts
            setattr(self, 'source', source.strip() if source else None),
            (
                setattr(self, 'user', user(self.source)),
                setattr(self, 'user', None) if self.user.nick is None else None,
            ) if self.source else setattr(self, 'user', None),
            setattr(self, 'cmd', cmd.strip().upper()),
            setattr(self, 'params', [p.strip() for p in params] if params else None),
            setattr(self, 'msg', msg.strip() if msg else None),
            setattr(self, 'invalid', True) if not self.msg_re.match(str(self)) else None,
        ),
    }
)

client = type(
    'client',
    (object,),
    {
        '__init__': lambda self, host, port=6667: ( # irc client object
            (
                setattr(self, 'host', host),
                setattr(self, 'port', int(port)),
                setattr(self, 'inthread', None),
                setattr(self, 'outthread', None),
                setattr(self, 'sock', None),
                setattr(self, 'nick', 'irc'),
                self.handlers.add(self.handle_ping),
                self.handlers.add(self.handle_ctcp),
                self.handlers.add(self.handle_nick),
                self.handlers.add(self.handle_join),
                self.handlers.add(self.handle_part),
                self.handlers.add(self.handle_kick),
                (lambda Queue: (
                    setattr(self, 'inqueue', Queue.Queue()),
                    setattr(self, 'outqueue', Queue.Queue()),
                ))(__import__('Queue')),
                None,
            )[-1]
        ),
        '__iter__': lambda self: ( # iterate through messages, blocking when waiting for one
            iter(self.inqueue.get, -1)
        ),
        '__str__': lambda self: ( # same as str(self.last), returns the last message read
            str(self.last)
        ),
        '__repr__': lambda self: (
            '<client %r:%r>' % (self.host, self.port)
        ),
        '_reader': lambda self: (
            (lambda f: (
                [self._handle(message(line)) for line in f]
            ))(self.sock.makefile()),
            None,
        )[-1],
        '_writer': lambda self: (
            (lambda f: (
                [(
                    f.write(str(msg)),
                    f.flush(),
                    setattr(msg, 'user', None),
                    self._handle(msg),
                    self.outqueue.task_done(),
                    None,
                )[-1] for msg in iter(self.outqueue.get, -1)]
            ))(self.sock.makefile()),
            None,
        )[-1],
        '_handle': lambda self, msg: (
            (
                setattr(self, 'last', msg),
                [h(self, msg) for h in self.handlers],
                self.inqueue.put(msg),
            ) if not msg.invalid else None
        ),
        'last': None, # the last message read
        'handlers': set(), # calls each of these functions with parameters (self, message) for each message read
        'channels': set(), # autojoins on start
        'start': lambda self, nickname, username, realname: ( # connects to server, starts read and write threads, sends NICK and USER and joins channels in self.channels; returns and sets self.work to False if nick is taken
            (lambda threading, socket: (
                self.stop(),
                setattr(self, 'work', True),
                setattr(self, 'nick', nickname),
                setattr(self, 'sock', socket.socket(socket.AF_INET, socket.SOCK_STREAM)),
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),
                self.sock.connect((self.host, self.port)),
                setattr(self, 'inthread', threading.Thread(target=self._reader)),
                setattr(self, 'outthread', threading.Thread(target=self._writer)),
                setattr(self.inthread, 'daemon', True),
                setattr(self.outthread, 'daemon', True),
                self.inthread.start(),
                self.outthread.start(),
                self.inqueue.get(),
                self.set_nick(nickname),
                self.login_user(username, realname),
                [_ for _ in ((lambda msg: iter('').next() if msg.cmd == '001' else ((setattr(self, 'work', False), setattr(self, 'last', msg), iter('').next()) if msg.cmd == '433' else None))(self.inqueue.get()) for i in xrange(10))],
                (
                    [self.join(ch) for ch in self.channels],
                ) if self.work else (
                    self.inqueue.put(self.last),
                    self.stop(),
                )
            ))(__import__('threading'), __import__('socket'))
        ),
        'stop': lambda self: ( # should stop the read/write threads and disconnect
            (
                setattr(self, 'work', False),
                self.inqueue.put(-1),
                self.outqueue.put(-1), 
            ) if getattr(self, 'work', False) else None
            (
                self.sock.shutdown(__import__('socket').SHUT_RDWR),
                self.sock.close(),
            ) if self.sock is not None else None,
            self.inthread.join() if self.inthread is not None and self.inthread.is_alive() else None,
            self.outthread.join() if self.outthread is not None and self.outthread.is_alive() else None,
            setattr(self, 'sock', None),
        ),
        'handle_ping': lambda self, client, msg: ( # respond to PINGs
            (
                client.send(message(None, 'PONG', msg.params, msg.msg))
            ) if msg.cmd == 'PING' else None,
        ),
        'ctcp': { # default CTCP responses; set any to None to disable
            'VERSION': lambda client, msg: 'irc',
            'PING': lambda client, msg: 'PING ' + msg if msg else 'PING',
            'TIME': (lambda time: lambda client, msg: time.asctime())(__import__('time')),
            'USERINFO': lambda client, msg: 'irc',
            'CLIENTINFO': lambda client, msg: ' '.join(k for k, v in client.ctcp.items() if v is not None),
        },
        'handle_ctcp': lambda self, client, msg: ( # handles CTCP requests, see client.ctcp dict for specific requests
            (lambda request, cmsg=None: (
                client.send(message(None, 'NOTICE', [msg.user.nick], '\001%s %s\001' % (request.upper(), self.ctcp[request.upper()](client, cmsg)))) if client.ctcp.get(request.upper(), None) is not None else None
            ))(*self.split_ctcp(msg.msg)) if msg.cmd == 'PRIVMSG' and self.is_ctcp(msg.msg) and msg.user else None
        ),
        'handle_invite': lambda self, client, msg: ( # automatically accepts invites
            (
                client.join(msg)
            ) if msg.cmd == 'INVITE' and msg.params and len(msg.params) == 2 and msg.params[0] == client.nick and msg.user else None
        ),
        'handle_nick': lambda self, client, msg: ( # keeps track of own nick changes
            (
                setattr(client, 'nick', msg.params[0])
            ) if msg.cmd == 'NICK' and msg.params and len(msg.params) == 1 and msg.user and msg.user.nick == client.nick else None
        ),
        'handle_join': lambda self, client, msg: ( # keeps track of own channel joins
            (
                client.channels.add(msg.params[0])
            ) if msg.cmd == 'JOIN' and msg.params and len(msg.params) == 1 and msg.user and msg.user.nick == client.nick else None
        ),
        'handle_part': lambda self, client, msg: ( # keeps track of own channel parts
            (
                client.channels.remove(msg.params[0]) if msg.params[0] in client.channels else None
            ) if msg.cmd == 'PART' and msg.params and len(msg.params) == 1 and msg.user and msg.user.nick == client.nick else None
        ),
        'handle_kick': lambda self, client, msg: ( # keeps track of being kicked
            (
                client.channels.remove(msg.params[0]) if msg.params[0] in client.channels else None
            ) if msg.cmd == 'KICK' and msg.params and len(msg.params) == 1 and msg.user and msg.msg == client.nick else None
        ),
        'is_ctcp': lambda self, s: (
            s is not None and len(s) > 0 and s[0] == '\001' and s[-1] == '\001'
        ),
        'split_ctcp': lambda self, s: (
            s[1:-1].split(None, 1)
        ),
        'send': lambda self, msg: ( # sends a message or raw irc string
            self.outqueue.put(msg if isinstance(msg, message) else message(msg)),
        ),
        'say': lambda self, where, msg: ( # sends a privmsg
            self.send(message(None, 'PRIVMSG', [where], msg))
        ),
        'join': lambda self, ch, key=None: ( # joins a channel
            self.send(message(None, 'JOIN', [ch] if key is None else [ch, key], None))
        ),
        'set_nick': lambda self, nick: ( # changes nick
            self.send(message(None, 'NICK', [nick], None))
        ),
        'login_user': lambda self, username, real: ( # USER command
            self.send(message(None, 'USER', [username, '8', '*'], real))
        ),
        'notice': lambda self, where, msg: ( # sends a notice
            self.send(message(None, 'NOTICE', [where], msg))
        ),
    }
)
