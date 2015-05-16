from twisted.python.rebuild import rebuild
import mumble_client as mc
import mumble_protocol as mp
import peebot
import datetime, os, time, sys
from threading import Timer


OWNER = "crusherexe"  # Your mumble nickname
SERVER_IP = "mumble.superphage.us"  # Server IP
SERVER_PORT = 64738  # Server PORT
USERNAME = "MasterBot"  # Bot's name

# Use empty string for optional fields to remove
PASSWORD = "not124"  # Optional password
CERTIFICATE = "master.p12"  # Optional certificate

USERFILE = "user.log" #Where user log is stored
BASELOG = "chat.log" #Where chat log is stored
DEBUGLOG = "debug.log" #Where debug information is stored

newLineChars = ["\n", "\r", "\n\r", "\r\n"] #Linux uses \n Windows uses \n\r


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
        self.startTime = self.getTime(True, True)
        self.timer = (datetime.datetime.now() + datetime.timedelta(0,2)).time()
        self.t = Timer(10.0, self.moveToAfk)
        self.debug = False
        self.debugFile = open(DEBUGLOG, "a")
        f = open(USERFILE, "w")
        f.write("")
        f.close()

    def reload(self):
        rebuild(mp)
        rebuild(peebot)

    #Check if a user has not been active in a certain amount of time
    #and moves them to afk if they are not active
    def moveToAfk(self):
        people = {}
        for id in self.users:
            people[self.users[id]] = id
        if not self.move:
            if self.debug:
                self.debugFile.write("Moving is turned off\n")
        else:
            myFile = open(USERFILE, "r")
            for line in myFile:
                if line in newLineChars:
                    continue
                lines = line.split("||")
                if self.debug:
                    self.debugFile.write("Checking: ")
                    self.debugFile.write(lines[0])
                    self.debugFile.write("\n")
                if lines[0] in self.users.values():
                    if self.debug:
                        self.debugFile.write("User is currently logged in\n")
                    if lines[1] != 'afk':
                        if self.debug:
                            self.debugFile.write("User is not in afk\n")
                        try:
                            times = self.getTimeFromLog(None, "lastActive", people[lines[0]]).split('::')
                            date = times[0]
                            curTime = times[1]
                            date = time.strptime(date, "%Y-%m-%d")
                            curTime = time.strptime(curTime.split('.')[0], "%H:%M:%S")
                            curTime = datetime.datetime(date[0], date[1], date[2], curTime[3], curTime[4], curTime[5])
                            date = datetime.date(date[0], date[1], date[2])
                            if date == datetime.datetime.now().date():
                                if curTime + datetime.timedelta(0, 1200) < datetime.datetime.now():
                                    if self.debug:
                                        self.debugFile.write("User has not been active for 1200 seconds\n")
                                    self.move_user(1, people[lines[0]])
                                elif self.debug:
                                    self.debugFile.write("Same date, but they have been active in the last 1200 seconds\n")
                            #If I have 10 people on at 11:59 p.m. and it changes to 12 of the next day
                            #the bot will? move everybody to afk UNTESTED
                            elif date < datetime.datetime.now().date():
                                if self.debug:
                                    self.debugFile.write("User has not been active?\n")
                                self.move_user(1, people[lines[0]])
                            elif self.debug:
                                self.debugFile.write("The user is in the future (by date), spooky\n")
                        except:
                            print lines[0]
            if self.debug:
                self.debugFile.write("\n")
            self.t = Timer(10.0, self.moveToAfk).start()

    #Send a message to a user/channel
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
        try:
            del self.users[p.session]
        except:
            print "Couldn't delete users session"

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

    #Returns date and/or time, if both are returned :: is put in between
    def getTime(self, date, time):
        retString = ""
        if date:
            retString+= str(datetime.datetime.now().date())
            if time:
                retString+= "::"
        if time:
            retString+= str(datetime.datetime.now().time())
        return retString

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
        userLine = ""
        myFile = open(USERFILE, "r")
        for line in myFile:
            if line in newLineChars:
                userLineinue
            lines = line.split("||")
            #returning user/updating status
            if self.users[p.actor] == lines[0]:
                found = True

                #user name
                userLine+= lines[0]
                userLine+= "||"

                #messages have channel_id as an array, states have them as an int
                if isinstance(p.channel_id, int):
                    userLine+= self.channels[p.channel_id]
                else:
                    userLine+= self.channels[p.channel_id[0]]
                userLine+= "||"

                #If they just logged in
                if new == True:
                    userLine+= self.getTime(True, True)
                else:
                    userLine+= lines[2]
                userLine+= "||"

                #if they logged out
                if new == "delete":
                    userLine+= self.getTime(True, True)
                else:
                    userLine+= lines[3]
                userLine+= "||"

                #last active
                userLine+= self.getTime(True, True)
                userLine+= "||"

                #channel state is int if moving channels, therefore this checks
                if p.__class__.__name__ == "UserState":
                    #They just came to SuperPhage
                    if not p.channel_id:
                        userLine+= lines[5] + "||"
                        userLine+=  self.getTime(True, True)

                    #They just left SuperPhage
                    else:   
                        userLine+= self.getTime(True, True) + "||"
                        userLine+= lines[6].replace("\n", "")
                else:
                    userLine+= lines[5] + "||"
                    userLine+= lines[6].replace("\n", "")

                userLine+= "\n"

            #Not the user, just replace the line
            else:
                userLine+= line

        myFile.close()
        myFile = open(USERFILE, "w")

        #New User
        if(found == None):
            #user name
            userLine+= self.users[p.actor]
            userLine+= "||"

            #channel name
            if isinstance(p.channel_id, int):
                userLine+= self.channels[p.channel_id]
            else:
                userLine+= self.channels[p.channel_id[0]]
            userLine+= "||"
            
            #logged on
            userLine+= self.getTime(True, True)
            userLine+= "||"

            #logged off
            userLine+= "0||"

            #last active
            userLine+= self.getTime(True, True)
            userLine+= "||"

            #last left channel
            userLine+= "0||"

            #came channel
            userLine+= "0"

            userLine+= "\n"
        myFile.write(userLine)
        myFile.close()

    #Returns Channel/Logged on Time/Last activity time/Last disconnected/Left channel/Came to root
    def getTimeFromLog(self, p, what, name = None):
        myFile = open(USERFILE, "r")
        if p:
            name = p.actor
        else:
            people = {}
            for id in self.users:
                people[self.users[id]] = id
            try:
                int(name)
            except:
                name = people[name]

        for line in myFile:
            if line in newLineChars:
                continue
            lines = line.split("||")
            if lines[0] != self.users[name]:
                continue
            if what == "channel":
                return lines[1]
            elif what == "loggedOnTime":
                return lines[2]
            elif what == "loggedOffTime":
                return lines[3]
            elif what == "lastActive":
                return lines[4]
            elif what == "leftChannel":
                return lines[5]
            elif what == "cameChannel":
                return lines[6]
        return None

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
                        msg+= " was last active at " + self.getTimeFromLog(None, "lastActive", name).split("::")[1][:-7]
                    else:
                        msg+= " is not online and was last seen in the channel " + lines[1] + " on " + self.getTimeFromLog(p, "loggedOffTime").replace("::", " at")[:-7]
                        
                if(type == "Online"):
                    if online:
                        msg+= " is online and was last active at " + self.getTimeFromLog(None, "lastActive", name).split("::")[1][:-7]
                    else:
                        msg+= " was last seen in the channel " + lines[1] + " on " + self.getTimeFromLog(None, "loggedOffTime", name).replace("::", " at ")[:-7]
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
        #curDate = datetime.date(date[0], date[1], date[2])
        #curDate = str(curDate)[:-3] + ":"
        curDate = str(date[0]) + "-" + str(date[1]) + ":"
        return curDate

    def getLastStatus(self, p, status):
        if status == "Online":
            temp = self.getTimeFromLog(p, "loggedOffTime")
        else:
            temp =  self.getTimeFromLog(p, "leftChannel")
        if temp != "0":
            return temp
        else:
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
        i = 0
        #if there is no difference in year
        if not (int(oldFile.split('-')[0]) - int(currentFile.split('-')[0])):
            #iterating over first week to current week
            for x in range((int(newWeeks) - int(oldWeeks) + 1)):
                #if the week number is one digit, prepend a zero
                if len(str(int(oldWeeks) + x)) == 1:
                    week = "0" + str(int(oldWeeks) + x)
                else:
                    week = str(int(oldWeeks) + x)
                #currentLog = Year-Week:
                currentLog = oldFile.split('-')[0] + "-" + week + ":"
                #YYYY-WW:chat.log
                if os.path.isfile(currentLog + BASELOG):
                    myFile = open(currentLog + BASELOG, "r")
                    #If we are in the first file
                    for i, line in enumerate(myFile):
                        if line in newLineChars: 
                            continue
                        lines = line.split("!||!")
                        #Getting the time to grab up too
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
        if response == "" and i == 0:
            response = "No unseen messages"
        else:
            self.reply(p, response, True)

    def handle_textmessage(self, p):
        try:
            self.userUpdate(p, None)
        except:
            print "Could not update user state" 

        #if p.message.startswith("/steve"):
        #    self.debugFile.write("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||")

        #Displays all available commands
        if p.message.startswith("/help"):
            self.reply(p, "<p>/active [username] will display when the user was last active</p><p>/online [username] will display when the user was last online</p><p>/log online will display all messages since you were last online</p><p>/log channel will display all messages since you left the root channel</p><p>/bot online will display the time the bot came online", True)

        if p.message.startswith("/log"):
            msg = p.message.split()
            if len(msg) > 1:
                if msg[1] == "online":
                    seenDate = self.getLastStatus(p, "Online")
                    if seenDate:
                        temp = time.strptime(seenDate.split("::")[0], "%Y-%m-%d")
                        onlineFile  = self.begWeek(datetime.date(temp[0], temp[1], temp[2]).isocalendar())
                        currentWeek = self.getTimeFromLog(p, "loggedOnTime")
                        currentTime = currentWeek.split("::")[1]
                        currentWeek = currentWeek.split("::")[0]
                        temp = time.strptime(currentWeek.split("::")[0], "%Y-%m-%d")
                        currentWeek = self.begWeek(datetime.date(temp[0], temp[1], temp[2]).isocalendar())
                        self.getLogMessage(p, onlineFile, seenDate, currentWeek, currentTime, seenDate.split("::")[0])
                    else:
                        self.reply(p, "You have never been seen logging off", True)
                elif msg[1] == "channel":
                    seenDate = self.getLastStatus(p, "Afk")
                    if seenDate:
                        temp = time.strptime(seenDate.split("::")[0], "%Y-%m-%d")
                        onlineFile = self.begWeek(datetime.date(temp[0], temp[1], temp[2]).isocalendar())
                        currentWeek = self.getTimeFromLog(p, "cameChannel")
                        currentTime = currentWeek.split("::")[1]
                        currentWeek = currentWeek.split("::")[0]
                        temp = time.strptime(currentWeek.split("::")[0], "%Y-%m-%d")
                        currentWeek = self.begWeek(datetime.date(temp[0], temp[1], temp[2]).isocalendar())
                        self.getLogMessage(p, onlineFile, seenDate, currentWeek, currentTime, seenDate.split("::")[0])
                    else:
                        self.reply(p, "You have never been seen in a differnet channel", True)

        if p.message.startswith("/bot online"):
            self.reply(p, str(self.startTime).replace("::", " at ").split(".")[0])

        #Displays when user was last active
        if p.message.startswith("/active"):
            if len(p.message.split()) > 1:
                response = self.getLast(p.message.split(' ')[-1],  "Active")
                if not response:
                    self.reply(p, "Invalid Name")
                else:
                    self.reply(p, response)

        #Displays when user was last online
        if p.message.startswith("/online"):
            if len(p.message.split()) > 1:
                response = self.getLast(p.message.split(' ')[-1],  "Online")
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

        if p.message == "/kill":
            self.move = None
            sys.exit()

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

        elif p.message == "/debug":
            if self.debug:
                self.debug = None
            else:
                self.debug = True

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
