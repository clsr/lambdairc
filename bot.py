# an example IRC bot using lambdairc.py

import lambdairc

def greeter(client, msg):
    if msg.cmd == 'JOIN' and msg.params and msg.user and msg.user.nick != client.nick:
        client.say(msg.params[0], 'Welcome, %s!' % msg.user.nick)

bot = lambdairc.client('irc.example.net')
bot.handlers.add(greeter)
bot.channels.add('#example')
bot.start('example', 'example', 'example')
for msg in bot:
    print msg,
