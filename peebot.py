from twisted.python.rebuild import rebuild
import mumble_client as mc
import mumble_protocol as mp
import peebot
import datetime, os, time


OWNER = "othercrusherexe"  # Your mumble nickname
SERVER_IP = "mumble.superphage.us"  # Server IP
SERVER_PORT = 64738  # Server PORT
USERNAME = "MasterBot"  # Bot's name

# Use empty string for optional fields to remove
PASSWORD = "not124"  # Optional password
CERTIFICATE = ""  # Optional certificate

USERFILE = "user.log" #Where user log is stored
BASELOG = "chat.log" #Where chat log is stored


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
        self.timer = (datetime.datetime.now() + datetime.timedelta(0,2)).time()

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
        #Checks every two seconds if a person is talking
        if (datetime.datetime.now().time() > self.timer):
            self.userUpdate(p, None)
            (datetime.datetime.now() + datetime.timedelta(0,2)).time()

    def handle_channelstate(self, p):
        if p.name:
            self.channels[p.channel_id] = p.name

    def handle_userremove(self, p):
        # Remove user from userlist
        self.userUpdate(p, "delete")
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
        #p.actor is 0 if it is a state change, messages don't have a p.session var
        if p.actor == 0:
            p.actor = p.session
        if p.channel_id == -1:
            p.channel_id = p.target
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
                #If they just logged in/logged out
                if new:
                    cont+= str(datetime.datetime.now().date()) + "::" + str(datetime.datetime.now().time())
                else:
                    cont+= lines[2]
                cont+= "||"
                cont+= str(datetime.datetime.now().date()) + "::" + str(datetime.datetime.now().time())
                cont+= "||"
                #if they logged out
                if new == "delete":
                    cont+= str(datetime.datetime.now().date()) + "::" + str(datetime.datetime.now().time())
                else:
                    cont+= lines[4].replace("\n", '')
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
            cont+= "||"
            cont+= "0"
            cont+= "\n"
        myFile.write(cont)
        myFile.close()

    #Displays when a user was last active/online
    def getLast(self, name, type):
        found = None
        myFile = open(USERFILE, "r")
        for line in myFile:
            if line == "\n" or line == "\n\r" or line == "\r": 
                continue
            lines = line.split("||")
            #returning user/updating status
            if name == lines[0]:
                found = True
                online = None
                for user in self.users:
                    if name ==  self.users[user]:
                        online = True
                msg = name
                if(type == "Active"):
                    if online:
                        msg+= " was last active at " + lines[3].split("::")[1][:-7]
                    else:
                        msg+= " is not online and was last seen in the channel " + lines[1] + " on " + lines[2].replace("::", " at")[:-7]
                        
                if(type == "Online"):
                    if online:
                        msg+= " is online and was last active at " + lines[3].split("::")[1][:-7]
                    else:
                        msg+= " was last seen in the channel " + lines[1] + " on " + lines[2].replace("::", " at ")[:-7]
                break
        myFile.close()
        if not found:
            return None
        else:
            return msg

    def logMsg(self, msg):
        week = self.begWeek(datetime.datetime.now().date().isocalendar())
        if os.path.isfile(week + BASELOG):
            myFile = open(week + BASELOG, "a")
        else:
            myFile = open(week + BASELOG, "w")
        myFile.write(msg + "\n")
        myFile.close()

    def begWeek(self, date):
        curDate = datetime.date(date[0], date[1], date[2])
        curDate = str(curDate)[:-3] + ":"
        return curDate

    def getLastOnline(self, p):
        myFile = open(USERFILE, "r")
        for line in myFile:
            if line == "\n" or line == "\n\r" or line == "\r": 
                continue
            lines = line.split("||")
            if lines[0] != self.users[p.actor]:
                continue
            else:
                if lines[4] == "0":
                    return None
                else:
                    return lines[4]

    def getLogMessage(self, oldFile, onlineTime, currentFile, currentTime):
        oldWeeks = oldFile.split('-')[1].replace(':', '')
        newWeeks = currentFile.split('-')[1].replace(':', '')
        response = ""
        if not (int(oldFile.split('-')[0]) - int(currentFile.split('-')[0])):
            for x in range((int(oldWeeks) - int(newWeeks)) + 1):
                currentLog = oldFile.split('-')[0] + "-" + str(int(oldWeeks) + x) + ":"
                if os.path.isfile(currentLog + BASELOG):
                    myFile = open(currentLog + BASELOG, "r")
                    for line in myFile:
                        if line == "\n" or line == "\n\r" or line == "\r": 
                            continue
                        lines = line.split("!||!")
                        response+= "<p>In " + lines[0] + " on " + lines[2] + " at " + lines[3][:-7] + " " + lines[1] + " said: " + lines[4] + "</p>"
                else:
                    print currentLog
        else:
            print (int(oldFile.split('-')[0]) - int(currentFile.split('-')[0]))
        return response


    def handle_textmessage(self, p):
        self.userUpdate(p, None)

        #Displays all available commands
        if p.message.startswith("/help"):
            self.reply(p, "<p>/active [username] will display when the user was last active<//p><p>/online [username] will display when the user was last online</p><p>/log online will display all messages since you were last online</p>")

        if p.message.startswith("/log"):
            msg = p.message.split()
            if msg[1] == "online":
                seenDate = self.getLastOnline(p)
                temp = time.strptime(seenDate.split("::")[0], "%Y-%m-%d")
                onlineFile = self.begWeek(datetime.date(temp[0], temp[1], temp[2]).isocalendar())
                onlineTime = seenDate.split("::")[1]
                currentWeek = self.begWeek(datetime.datetime.now().date().isocalendar())
                currentTime = datetime.datetime.now().time()
                self.reply(p, self.getLogMessage(onlineFile, onlineTime, currentWeek, currentTime))


        #Displays when user was last active
        if p.message.startswith("/active"):
            response = self.getLast(p.message.split(' ')[-1], "Active")
            if not response:
                self.reply(p, "Invalid Name")
            else:
                self.reply(p, response)

        #Displays when user was last online
        if p.message.startswith("/online"):
            response = self.getLast(p.message.split(' ')[-1], "Online")
            if not response:
                self.reply(p, "Invalid Name")
            else:
                self.reply(p, response)

        if self.loggingOn:
            p.message = p.message.replace("!||!", "!|!")
            self.logMsg(self.channels[p.channel_id[0]] + "!||!" + self.users[p.actor] + "!||!" + str(datetime.datetime.now().date()) + "!||!" + str(datetime.datetime.now().time()) + "!||!" + p.message)

        #ADMIN COMMANDS
        # Only listen to the owner
        if self.users[p.actor] != OWNER:
            return

        # Reload the script
        if p.message == "/reload":
            self.reload()
            self.send_textmessage("Reloaded!", p.channel_id)

        # Turnning on/off chat logging
        elif p.message == "/logging":
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
