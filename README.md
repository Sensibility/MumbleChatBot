MumbleChatBot
=============

Simple client written in Python that let's you create a bot and interact with a mumble server.
New version was written from the ground up and offers better API support for writing your bot.

The only dependency is [Twisted](http://twistedmatrix.com/trac/).

Currently, the client can:

- Auth and connect to a server using password or certificate
- Get user and channel states
- Get and send chat messages
- Get voice packets (through TCP only, UDP tunnel is not implemented yet)

There is no codec support though, so the audio data cannot be parsed.

Extension
=============

Peebot.py has been modified to allow for the following functionality:

- Automatic moving of users to a specified channel after a certian amount of inactive time
- Give detailed information about when a user was last seen, last active, last changed channels.
- Get a log of messages from the last time the user left the channel or logged off.
- Provide admin functionality to specific users without actually giving them admin priviledges.
