from twisted.python.rebuild import rebuild
import mumble_client as mc
import mumble_protocol as mp
import peebot
import datetime


OWNER = "othercrusherexe"  # Your mumble nickname
SERVER_IP = "mumble.superphage.us"  # Server IP
SERVER_PORT = 64738  # Server PORT
USERNAME = "MasterBot"  # Bot's name

# Use empty string for optional fields to remove
PASSWORD = "not124"  # Optional password
CERTIFICATE = ""  # Optional certificate

USERFILE = "user.log" #Where user log is stored


class PeeBotClient(mp.MumbleClient):
    def connectionMade(self):
        mp.MumbleClient.connectionMade(self)

        self.users = {}
        self.channels = {}
        self.session = 0
        self.channel = 3
        self.shutup = []
        self.follow = 0
        self.c_order = []
        self.loggingOn = True

    def reload(self):
        rebuild(mp)
        rebuild(peebot)

    def reply(self, p, msg):
        if p.channel_id:
            self.send_textmessage(msg, channels=p.channel_id)
        else:
            self.send_textmessage(msg, users=[p.actor])

    def handle_udptunnel(self, p):
        if self.users[p.session] in self.shutup:
            self.move_user(self.shutup_channel, p.session)

    def handle_channelstate(self, p):
        if p.name:
            self.channels[p.channel_id] = p.name

    def handle_userremove(self, p):
        # Remove user from userlist
        del self.users[p.session]

    def handle_userstate(self, p):
        # Add user id to the userlist
        update = None
        if p.name:
            update = True
            self.users[p.session] = p.name

        # Stores own session id
        if p.name == self.factory.nickname:
            self.session = p.session

        if p.session == self.session:
            self.channel = p.channel_id

        # Follows user around
        if self.users[p.session] == self.follow:
            if p.channel_id:
                self.move_user(p.channel_id, self.session)
            elif p.self_mute:
                self.mute_or_deaf(self.session, True, True)
            else:
                self.mute_or_deaf(self.session, False, False)
        self.userUpdate(p, update)

    def userUpdate(self, p, new):
        if p.actor == 0:
            p.actor = p.session
        if not p.actor in self.users:
            return
        else:
            if self.users[p.actor] == USERNAME:
                return
        found = None
        cont = ""
        myFile = open(USERFILE, "r")
        for line in myFile:
            if line == "\n" or line == "\n\r" or line == "\r": 
                continue
            lines = line.split("||")
            #returning user/updating status
            if self.users[p.actor] == lines[0]:
                found = True
                cont+= lines[0]
                cont+= "||"
                #messages have channel_id as an array, states have them as an int
                if isinstance(p.channel_id, int):
                    cont+= self.channels[p.channel_id]
                else:
                    cont+= self.channels[p.channel_id[0]]
                cont+= "||"
                #If they just logged in
                if new:
                    cont+= str(datetime.datetime.now().date()) + "::" + str(datetime.datetime.now().time())
                else:
                    cont+= lines[2]
                cont+= "||"
                cont+= str(datetime.datetime.now().date()) + "::" + str(datetime.datetime.now().time())
                cont+= "\n"
            else:
                cont+= line
        myFile.close()
        myFile = open(USERFILE, "w")
        #New User
        if(found == None):
            cont+= self.users[p.actor]
            cont+= "||"
            if isinstance(p.channel_id, int):
                cont+= self.channels[p.channel_id]
            else:
                cont+= self.channels[p.channel_id[0]]
            cont+= "||"
            cont+= str(datetime.datetime.now().date()) + "::" + str(datetime.datetime.now().time())
            cont+= "||"
            cont+= str(datetime.datetime.now().date()) + "::" + str(datetime.datetime.now().time())
            cont+= "\n"
        myFile.write(cont)
        myFile.close()

    def handle_textmessage(self, p):
        self.userUpdate(p, None)

        if self.loggingOn:
            p.message = p.message.replace("!||!", "!|!")
            print self.channels[p.channel_id[0]] + "!||!" + self.users[p.actor] + "!||!" + str(datetime.datetime.now().date()) + "!||!" + str(datetime.datetime.now().time()) + "!||!" + p.message

        #ADMIN COMMANDS
        # Only listen to the owner
        if self.users[p.actor] != OWNER:
            return

        # Reload the script
        if p.message == "/reload":
            self.reload()
            self.send_textmessage("Reloaded!", p.channel_id)

        # Turnning on/off chat logging
        elif p.message == "/log":
            if self.loggingOn:
                self.loggingOn = None
            else:
                self.loggingOn = True

        # Moves user every time they talk
        elif p.message.startswith("/shutup"):
            name = p.message.split(' ')[-1]
            if name in self.users.values():
                self.shutup_channel = 18
                self.shutup.append(name)
            else:
                self.reply(p, "Invalid name")

        elif p.message.startswith("/stop"):
            self.shutup = []

        # Follows user around different channels (and mute)
        elif p.message.startswith("/follow"):
            name = p.message.split(' ')[-1]
            if name in self.users.values():
                self.follow = name
            else:
                self.reply(p, "Invalid name")

        elif p.message.startswith("/unfollow"):
            self.follow = 0

        # List the channels in the console
        elif p.message.startswith("/channels"):
            print self.channels

        # List the users in the console
        elif p.message.startswith("/users"):
            print self.users


if __name__ == '__main__':
    factory = mc.create_client(peebot.PeeBotClient, USERNAME, PASSWORD)
    mc.start_client(factory, SERVER_IP, SERVER_PORT, certificate=CERTIFICATE)
