from twisted.python.rebuild import rebuild
import mumble_client as mc
import mumble_protocol as mp
import peebot
import datetime, os, time
from threading import Timer


OWNER = "othercrusherexe"  # Your mumble nickname
SERVER_IP = "mumble.superphage.us"  # Server IP
SERVER_PORT = 64738  # Server PORT
USERNAME = "MasterBot"  # Bot's name

# Use empty string for optional fields to remove
PASSWORD = "not124"  # Optional password
CERTIFICATE = "/home/crusherexe/master.p12"  # Optional certificate

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
        self.move = True
        self.timer = (datetime.datetime.now() + datetime.timedelta(0,2)).time()
        self.t = Timer(10.0, self.moveToAfk).start()

    def reload(self):
        rebuild(mp)
        rebuild(peebot)

    def moveToAfk(self):
        print "Checking..."
        people = {}
        for id in self.users:
            people[self.users[id]] = id
        if not self.move:
            print "Stopping"
        else:
            myFile = open(USERFILE, "r")
            for line in myFile:
                if line == "\n" or line == "\n\r" or line == "\r": 
                    continue
                lines = line.split("||")
                if lines[0] in self.users.values():
                    if lines[1] != 'afk':
                        times = lines[3].split('::')
                        date = times[0]
                        curTime = times[1]
                        date = time.strptime(date, "%Y-%m-%d")
                        curTime = time.strptime(curTime.split('.')[0], "%H:%M:%S")
                        curTime = datetime.datetime(date[0], date[1], date[2], curTime[3], curTime[4], curTime[5])
                        date = datetime.date(date[0], date[1], date[2])
                        if date == datetime.datetime.now().date():
                            if curTime + datetime.timedelta(0, 1200) < datetime.datetime.now():
                                self.move_user(1, people[lines[0]])
                        elif date < datetime.datetime.now().date():
                            self.move_user(1, people[lines[0]])
            self.t = Timer(10.0, self.moveToAfk).start()

    def reply(self, p, msg, pm = None):
        if pm:
            self.send_textmessage(msg, users=[p.actor])
            return
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
                cont+= "||"
                #channel state is int if moving channels, therefore this checks
                #if they have just moved to SuperPhage
                if p.channel_id and p.__class__.__name__ == "UserState":
                    cont+=  str(datetime.datetime.now().date()) + "::" + str(datetime.datetime.now().time())
                else:
                    cont+= lines[5].replace("\n", '')
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
            cont+= "||"
            cont+= "0"
            cont+= "||"
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

    def getLastStatus(self, p, status):
        myFile = open(USERFILE, "r")
        for line in myFile:
            if line == "\n" or line == "\n\r" or line == "\r": 
                continue
            lines = line.split("||")
            if lines[0] != self.users[p.actor]:
                continue
            else:
                if(status == "Online"):
                    if lines[4] == "0":
                        return None
                    else:
                        return lines[4]
                elif(status == "Afk"):
                    if lines[5] == "0\n":
                        return None
                    else:
                        return lines[5]
        return None

    def compareTime(self, time1, time2):
        if time1.tm_year > time2.tm_year:
            return True
        else:
            if time1.tm_mon > time2.tm_mon:
                return True
            else:
                if time1.tm_mday >time2.tm_mday:
                    return True
                else:
                    if time1.tm_hour > time2.tm_hour:
                        return True
                    else:
                        if time1.tm_min > time2.tm_min:
                            return True
                        else:
                            if time1.tm_sec > time2.tm_sec:
                                return True
                            else:
                                return None

    def getLogMessage(self, p, oldFile, seenDate, currentFile, newTime, newDay):
        oldWeeks = oldFile.replace(':', '').split('-')[1]
        newWeeks = currentFile.replace(':', '').split('-')[1]
        response = ""
        #if there is no difference in year
        if not (int(oldFile.split('-')[0]) - int(currentFile.split('-')[0])):
            #iterating over first week to current week
            for x in range((int(newWeeks) - int(oldWeeks) + 1)):
                if len(str(int(oldWeeks) + x)) == 1:
                    week = "0" + str(int(oldWeeks) + x)
                else:
                    week = str(int(oldWeeks) + x)
                currentLog = oldFile.split('-')[0] + "-" + week + ":"
                i = 0
                if os.path.isfile(currentLog + BASELOG):
                    myFile = open(currentLog + BASELOG, "r")
                    #If we are in the first file
                    for i, line in enumerate(myFile):
                        if line == "\n" or line == "\n\r" or line == "\r": 
                            continue
                        lines = line.split("!||!")
                        newComp = time.strptime(newDay + "::" + str(newTime).split(".")[0], "%Y-%m-%d::%H:%M:%S")
                        oldComp = time.strptime(seenDate.split(".")[0], "%Y-%m-%d::%H:%M:%S")
                        tempTime = time.strptime(lines[2] + "::" + lines[3].split(".")[0], "%Y-%m-%d::%H:%M:%S")
                        #on oldFile file, looking for start output
                        if not x and not (int(newWeeks) - int(oldWeeks)):
                            if self.compareTime(oldComp, tempTime):
                                continue
                        #If we are in the last file
                        if int(oldWeeks) + x == int(newWeeks):
                            if not self.compareTime(newComp, tempTime):
                                continue

                        response+= "<p>In " + lines[0] + " on " + lines[2] + " at " + lines[3][:-7] + " " + lines[1] + " said: " + lines[4] + "</p>"
                        #To avoid too large of a string
                        if i % 20 == 0:
                            self.reply(p, response, True)
                            response = ""
                else:
                    print "Doesn't exist: " + currentLog
        else:
            print (int(oldFile.split('-')[0]) - int(currentFile.split('-')[0]))
        if response == "" and i != 0:
            response = "No unseen messages"
        else:
            self.reply(p, response, True)


    def handle_textmessage(self, p):
        self.userUpdate(p, None)

        #Displays all available commands
        if p.message.startswith("/help"):
            self.reply(p, "<p>/active [username] will display when the user was last active</p><p>/online [username] will display when the user was last online</p><p>/log online will display all messages since you were last online</p><p>/log channel will display all messages since you left the root channel</p>", True)

        if p.message.startswith("/log"):
            msg = p.message.split()
            if len(msg) > 1:
                if msg[1] == "online":
                    seenDate = self.getLastStatus(p, "Online")
                    if seenDate:
                        print seenDate
                        temp = time.strptime(seenDate.split("::")[0], "%Y-%m-%d")
                        onlineFile = self.begWeek(datetime.date(temp[0], temp[1], temp[2]).isocalendar())
                        currentWeek = self.begWeek(datetime.datetime.now().date().isocalendar())
                        currentTime = datetime.datetime.now().time()
                        self.getLogMessage(p, onlineFile, seenDate, currentWeek, currentTime, seenDate.split("::")[0])
                    else:
                        self.reply(p, "You have never been seen logging off", True)
                elif msg[1] == "channel":
                    seenDate = self.getLastStatus(p, "Afk")
                    if seenDate:
                        temp = time.strptime(seenDate.split("::")[0], "%Y-%m-%d")
                        onlineFile = self.begWeek(datetime.date(temp[0], temp[1], temp[2]).isocalendar())
                        currentWeek = self.begWeek(datetime.datetime.now().date().isocalendar())
                        currentTime = datetime.datetime.now().time()
                        self.getLogMessage(p, onlineFile, seenDate, currentWeek, currentTime, seenDate.split("::")[0])
                    else:
                        self.reply(p, "You have never been seen in a differnet channel", True)


        #Displays when user was last active
        if p.message.startswith("/active"):
            if len(p.message.split() > 1):
                response = self.getLast(p.message.split(' ')[-1], "Active")
                if not response:
                    self.reply(p, "Invalid Name")
                else:
                    self.reply(p, response)

        #Displays when user was last online
        if p.message.startswith("/online"):
            if len(p.message.split() > 1):
                response = self.getLast(p.message.split(' ')[-1], "Online")
                if not response:
                    self.reply(p, "Invalid Name")
                else:
                    self.reply(p, response)

        if self.loggingOn and not p.message.startswith("/log"):
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

        if p.message == "/afk":
            if self.move:
                self.move = None
            else:
                self.move = True
                self.t = Timer(10.0, self.moveToAfk).start()

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
