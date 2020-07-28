# -*- coding: utf-8 -*-
import sys
import re
import socket
import time
import struct
import select
import errno

from fcreplay.chat.protocol import Protocol

import logging
import json
from fcreplay.chat.player import Player
from fcreplay.chat.playerstate import PlayerStates

from threading import Thread

from fcreplay.getplayerreplay import main as getfcplayerreplay
import fcreplay.jobstatus as fcjobstatus

with open("config.json") as json_data_file:
    config = json.load(json_data_file)

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    filename=config['logfile'],
    level=config['loglevel'],
    datefmt='%Y-%m-%d %H:%M:%S'
)


class Controller():
    emitList = []
    __versionNum__ = 42

    (STATE_TCP_READ_LEN, STATE_TCP_READ_DATA) = range(2)

    def __del__(self):
        # noinspection PyBroadException
        try:
            self.tcpSock.close()
            self.udpSock.close()
        except:
            pass

    def __init__(self):
        super(Controller, self).__init__()
        self.selectTimeout = 1
        self.sequence = 0x1
        self.tcpSock = None
        self.tcpConnected = False
        self.tcpData = b''
        self.tcpReadState = self.STATE_TCP_READ_LEN
        self.tcpResponseLen = 0
        self.tcpCommandsWaitingForResponse = dict()
        self.udpSock = None
        self.udpConnected = False
        self.selectLoopRunning = True
        self.switchingServer = False

        self.username = ''
        self.password = ''
        self.channel = 'lobby'
        self.channelport = 7000
        self.rom = ''
        self.playingagainst = ''

        self.challengers = set()
        self.challenged = None
        self.channels = {}
        self.pinglist = {}
        self.players = {}
        self.available = {}
        self.playing = {}
        self.awayfromkb = {}

        self.stateChannelIsLoaded = False

        self.tcpPort = 7000
        self.udpPort = 6009

        # Used to send advertisement every hour, or 20seconds after startup
        self.advertiseTimeSent = (int(time.time()) - 3580)

    def addUser(self, **kwargs):
        if 'player' in kwargs:
            name = kwargs['player']
            if name not in self.available and name not in self.awayfromkb and name not in self.playing:
                self.emitList.append(
                    {
                        'state': 'newlyJoined',
                        'name': name
                    }
                )
            if name in self.players:
                p = self.players[name]
            else:
                p = Player(**kwargs)
                self.players[name] = p

    def connectTcp(self):
        self.tcpConnected = False
        # noinspection PyBroadException
        try:
            if self.tcpSock:
                self.tcpSock.close()
            self.tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.channelport = self.tcpPort
            if self.channelport == None:
                self.channelport = 7000
            self.tcpSock.connect(('ggpo-ng.com', int(self.channelport),))
            self.tcpConnected = True
        except Exception:
            self.emitList.append(
                {
                    'state': 'exception',
                    'message': 'Cannot connect to FightCade server'
                }
            )
            self.emitList.append(
                {
                    'state': 'disconnect'
                }
            )
        return self.tcpConnected

    def dispatch(self, seq, data):
        logging.debug(
            'Dispatch ' + Protocol.outOfBandCodeToString(seq) + ' ' + repr(data)
        )
        # out of band data
        if seq == Protocol.CHAT_DATA:
            self.parseChatResponse(data)
        elif seq == Protocol.PLAYER_STATE_CHANGE:
            self.parseStateChangesResponse(data)
        elif seq == Protocol.CHALLENGE_DECLINED:
            pass
        elif seq == Protocol.CHALLENGE_RECEIVED:
            pass
        elif seq == Protocol.CHALLENGE_RETRACTED:
            pass
        elif seq == Protocol.JOINING_A_CHANNEL:
            self.parseJoinChannelResponse(data)
        elif seq == Protocol.SPECTATE_GRANTED:
            pass
        else:
            # in band response to our previous request
            self.dispatchInbandData(seq, data)

    def dispatchInbandData(self, seq, data):
        if not seq in self.tcpCommandsWaitingForResponse:
            logging.error("Sequence {} data {} not matched".format(seq, data))
            return

        origRequest = self.tcpCommandsWaitingForResponse[seq]
        del self.tcpCommandsWaitingForResponse[seq]

        if origRequest == Protocol.AUTH:
            self.parseAuthResponse(data)
        elif origRequest == Protocol.MOTD:
            self.parseMotdResponse(data)
        elif origRequest == Protocol.LIST_CHANNELS:
            self.parseListChannelsResponse(data)
        elif origRequest == Protocol.LIST_USERS:
            self.parseListUsersResponse(data)
        elif origRequest == Protocol.SPECTATE:
            status, data = Protocol.extractInt(data)
            if status != 0:
                self.emitList.append(
                    {
                        'state': 'error',
                        'message': f'Failed to spectate {status}'
                    }
                )
        elif origRequest in [Protocol.WELCOME, Protocol.JOIN_CHANNEL, Protocol.TOGGLE_AFK,
                             Protocol.SEND_CHALLENGE, Protocol.CHAT, Protocol.ACCEPT_CHALLENGE,
                             Protocol.DECLINE_CHALLENGE, Protocol.CANCEL_CHALLENGE]:
            if len(data) == 4:
                status, data = Protocol.extractInt(data)
                if status != 0:
                    codestr = Protocol.codeToString(origRequest)
                    logging.error(
                        "{} failed, data {}".format(codestr, repr(data))
                    )
                    if codestr == "SEND_CHALLENGE":
                        self.emitList.append(
                            {
                                'state': 'error',
                                'message': 'SEND_CHALLANGE failed'
                            }
                        )
                    elif codestr == "CANCEL_CHALLENGE":
                        pass
                    else:
                        self.emitList.append(
                            {
                                'state': 'error',
                                'message': f'codestr: {codestr}'
                            }
                        )
            else:
                logging.error("Unknown response for {}; seq {}; data {}".format(
                    Protocol.codeToString(origRequest), seq, repr(data)))
        else:
            logging.error("Not handling {} response; seq {}; data {}".format(
                Protocol.codeToString(origRequest), seq, repr(data)))

    @staticmethod
    def extractStateChangesResponse(data):
        if len(data) >= 4:
            code, data = Protocol.extractInt(data)
            p1, data = Protocol.extractTLV(data)
            if code == 0:
                p2 = ''
                return PlayerStates.QUIT, p1, p2, None, data
            elif code != 1:
                logging.error(
                    "Unknown player state change code {}".format(code)
                )
            state, data = Protocol.extractInt(data)
            p2, data = Protocol.extractTLV(data)
            if not p2:
                p2 = "null"
            ip, data = Protocol.extractTLV(data)
            # \xff\xff\xff\x9f
            # \x00\x00\x00&
            unknown1, data = Protocol.extractInt(data)
            unknown2, data = Protocol.extractInt(data)
            city, data = Protocol.extractTLV(data)
            cc, data = Protocol.extractTLV(data)
            if cc:
                cc = cc.lower()
            country, data = Protocol.extractTLV(data)
            # \x00\x00\x17y
            marker, data = Protocol.extractInt(data)
            playerinfo = dict(
                player=p1,
                ip=ip,
                city=city,
                cc=cc,
                country=country,
                spectators=0,
            )
            return state, p1, p2, playerinfo, data

    def handleTcpResponse(self):
        if self.tcpReadState == self.STATE_TCP_READ_LEN:
            if len(self.tcpData) >= 4:
                self.tcpResponseLen, self.tcpData = Protocol.extractInt(
                    self.tcpData
                )
                self.tcpReadState = self.STATE_TCP_READ_DATA
                self.handleTcpResponse()
        elif self.tcpReadState == self.STATE_TCP_READ_DATA:
            if len(self.tcpData) >= self.tcpResponseLen:
                # tcpResponseLen should be >= 4
                if self.tcpResponseLen < 4:
                    logging.error(
                        'Cannot handle TLV payload of less than 4 bytes'
                    )
                    self.tcpData = self.tcpData[self.tcpResponseLen:]
                    self.tcpResponseLen = 0
                    self.tcpReadState = self.STATE_TCP_READ_LEN
                    self.handleTcpResponse()
                else:
                    data = self.tcpData[:self.tcpResponseLen]
                    self.tcpData = self.tcpData[self.tcpResponseLen:]
                    seq = Protocol.unpackInt(data[0:4])
                    self.tcpResponseLen = 0
                    self.tcpReadState = self.STATE_TCP_READ_LEN
                    self.dispatch(seq, data[4:])
                    self.handleTcpResponse()

    def parseAuthResponse(self, data):
        if len(data) < 4:
            logging.error("Unknown auth response {}".format(repr(data)))
            return
        result, data = Protocol.extractInt(data)
        if result == 0:
            self.selectTimeout = 15
            self.emitList.append(
                {
                    'state': 'logingSuccess'
                }
            )
        else:
            if self.tcpSock:
                self.tcpSock.close()
                self.tcpConnected = False
            self.emitList.append(
                {
                    'state': 'statusMessage',
                    'message': f'login failed {result}'
                }
            )
            if result == 6:
                self.emitList.append(
                    {
                        'state': 'statusMessage',
                        'message': 'login failed wrong password'
                    }
                )
            elif result == 9:
                self.emitList.append(
                    {
                        'state': 'statusMessage',
                        'message': 'too many connections'
                    }
                )
            elif result == 4:
                self.emitList.append(
                    {
                        'state': 'statusMessage',
                        'message': 'Username doesns exist in database'
                    }
                )
            elif result == 8:
                self.emitList.append(
                    {
                        'state': 'statusMessage',
                        'message': 'Clone connection closed, please login again'
                    }
                )
            else:
                self.emitList.append(
                    {
                        'state': 'statusMessage',
                        'message': f'login failed {result}'
                    }
                )

    def parseChatResponse(self, data):
        name, data = Protocol.extractTLV(data)
        msg, data = Protocol.extractTLV(data)
        try:
            msg = msg.decode('utf-8')
            name = name.decode('utf-8')
        except ValueError:
            pass
        logging.debug(u"<{}> {}".format(name, msg))
        self.emitList.append(
            {
                'state': 'chatReceived',
                'message': str(msg),
                'name': str(name)
            }
        )

    # noinspection PyUnusedLocal
    def parseJoinChannelResponse(self, data):
        self.sigChannelJoined = True
        self.sendMOTDRequest()
        self.sendListUsers()

    def parseListChannelsResponse(self, data):
        if len(data) <= 8:
            logging.error('No channels found')
            self.stateChannelIsLoaded = True
            return
        status1, data = Protocol.extractInt(data)
        status2, data = Protocol.extractInt(data)
        logging.debug("Load channels header " + repr(status1) + repr(status2))
        while len(data) > 4:
            room, data = Protocol.extractTLV(data)
            romname, data = Protocol.extractTLV(data)
            title, data = Protocol.extractTLV(data)
            users, data = Protocol.extractInt(data)
            port, data = Protocol.extractInt(data)
            index, data = Protocol.extractInt(data)
            channel = {
                'rom': romname.decode("utf-8").split(':')[0],
                'room': room.decode("utf-8"),
                'title': title.decode("utf-8"),
                'users': users,
                'port': port,
            }
            self.channels[room.decode("utf-8")] = channel
        logging.debug(repr(self.channels))
        self.stateChannelIsLoaded = True
        if len(data) > 0:
            logging.error('Channel REMAINING DATA len {} {}'.format(
                len(data), repr(data))
            )

    def parseListUsersResponse(self, data):
        self.resetPlayers()
        if not data:
            return
        status, data = Protocol.extractInt(data)
        status2, data = Protocol.extractInt(data)
        while len(data) > 8:
            p1, data = Protocol.extractTLV(data)
            # if len(data) <= 4: break
            state, data = Protocol.extractInt(data)
            p2, data = Protocol.extractTLV(data)
            ip, data = Protocol.extractTLV(data)
            unk1, data = Protocol.extractInt(data)
            unk2, data = Protocol.extractInt(data)
            city, data = Protocol.extractTLV(data)
            cc, data = Protocol.extractTLV(data)
            if cc:
                cc = cc.lower()
            country, data = Protocol.extractTLV(data)
            port, data = Protocol.extractInt(data)
            spectators, data = Protocol.extractInt(data)
            self.addUser(
                player=p1,
                ip=ip,
                port=port,
                city=city,
                cc=cc,
                country=country,
                spectators=spectators+1,
            )
            if state == PlayerStates.AVAILABLE:
                self.available[p1] = True
            elif state == PlayerStates.AFK:
                self.awayfromkb[p1] = True
            elif state == PlayerStates.PLAYING:
                if not p2:
                    p2 = 'null'
                self.playing[p1] = p2
        self.emitList.append(
            {
                'state': 'playersLoaded',
            }
        )
        if len(data) > 0:
            logging.error(
                'List users - REMAINING DATA len {} {}'.format(len(data), repr(data))
            )

    def parseMotdResponse(self, data):
        if not data:
            return
        status, data = Protocol.extractInt(data)
        channel, data = Protocol.extractTLV(data)
        topic, data = Protocol.extractTLV(data)
        msg, data = Protocol.extractTLV(data)
        self.emitList.append(
            {
                'state': 'motdReceived',
                'channel': str(channel),
                'topic': str(topic),
                'message': str(msg)
            }
        )

    def parseStateChangesResponse(self, data):
        count, data = Protocol.extractInt(data)
        while count > 0 and len(data) >= 4:
            state, p1, p2, playerinfo, data = self.__class__.extractStateChangesResponse(
                data
            )
            msg = f'State: {state}, p1: {p1}, p2: {p2}, playerInfo: {playerinfo}, data: {data}'
            logging.debug(msg)
            count -= 1
        # if len(data) > 0:
        #    logging.error("stateChangesResponse, remaining data {}".format(repr(data)))

    def resetPlayers(self):
        self.available = {}
        self.playing = {}
        self.awayfromkb = {}

    def selectLoop(self):
        while self.selectLoopRunning:
            inputs = []
            if self.udpConnected:
                inputs.append(self.udpSock)
            if self.tcpConnected:
                inputs.append(self.tcpSock)
                # windows doesn't allow select on 3 empty set
            if not inputs:
                time.sleep(1)
                continue
            inputready, outputready, exceptready = None, None, None
            # http://stackoverflow.com/questions/13414029/catch-interrupted-system-call-in-threading
            try:
                inputready, outputready, exceptready = select.select(
                    inputs, [], [], self.selectTimeout
                )
            except select.error as ex:
                if ex[0] != errno.EINTR and ex[0] != errno.EBADF:
                    raise
            if not inputready:
                continue
            else:
                for stream in inputready:
                    if stream == self.tcpSock:
                        data = None
                        # noinspection PyBroadException
                        try:
                            data = stream.recv(16384)
                        except:
                            if not self.switchingServer:
                                self.tcpConnected = False
                                self.selectLoopRunning = False
                                self.emitList.append(
                                    {
                                        'state': 'serverDisconnected'
                                    }
                                )
                                return
                        if data:
                            self.tcpData += data
                            self.handleTcpResponse()
                        else:
                            if not self.switchingServer:
                                stream.close()
                                self.tcpConnected = False
                                self.selectLoopRunning = False
                                self.emitList.append(
                                    {
                                        'state': 'serverDisconnected'
                                    }
                                )
                    elif stream == self.udpSock:
                        dgram = None
                        try:
                            dgram, addr = self.udpSock.recvfrom(64)
                        except:
                            pass
                        if dgram:
                            logging.debug("UDP " + repr(dgram) +
                                          " from " + repr(addr)
                            )
                            self.handleUdpResponse(dgram, addr)

    def sendAndForget(self, command, data=b''):
        logging.debug('Sending {} seq {} {}'.format(
            Protocol.codeToString(command), self.sequence, repr(data))
        )
        self.sendtcp(struct.pack('!I', command) + data)

    def sendAndRemember(self, command, data=b''):
        logging.debug(
            f'Sending: {Protocol.codeToString(command)} seq: {self.sequence} repr: {repr(data)}'
        )
        self.tcpCommandsWaitingForResponse[self.sequence] = command
        self.sendtcp(struct.pack('!I', command) + data)

    def sendAuth(self, username, password):
        self.username = username
        try:
            port = self.udpSock.getsockname()[1]
        except:
            port = 6009
            # raise
        authdata = Protocol.packTLV(username) + Protocol.packTLV(password) + Protocol.packInt(port) + Protocol.packInt(self.__versionNum__)
        self.sendAndRemember(Protocol.AUTH, authdata)

    def sendChat(self, line):
        if self.channel == 'unsupported' and self.unsupportedRom:
            line = '[' + self.unsupportedRom + '] ' + line
        #line = line.encode('utf-8')
        self.sendAndRemember(Protocol.CHAT, Protocol.packTLV(line))

    def sendJoinChannelRequest(self, channel=None):
        if channel:
            self.channel = channel
            if channel in self.channels:
                if channel != 'lobby':
                    self.rom = self.channels[channel]['rom']
                else:
                    self.rom = ''
            else:
                logging.error("Invalid channel {}".format(channel))

        if (int(self.channelport) != int(self.channels[channel]['port'])):
            self.switchingServer = True
            self.channelport = int(self.channels[channel]['port'])
            self.tcpSock.close()
            self.sequence = 0x1
            self.connectTcp()
            self.sendWelcome()
            self.sendAuth(self.username, self.password)
        self.sendAndRemember(Protocol.JOIN_CHANNEL,
                             Protocol.packTLV(self.channel)
        )

    def sendListChannels(self):
        self.sendAndRemember(Protocol.LIST_CHANNELS)

    def sendListUsers(self):
        self.sendAndRemember(Protocol.LIST_USERS)

    def sendMOTDRequest(self):
        self.sendAndRemember(Protocol.MOTD)
        self.switchingServer = False

    def sendWelcome(self):
        self.sendAndRemember(
            Protocol.WELCOME, b'\x00\x00\x00\x00\x00\x00\x00\x1d\x00\x00\x00\x01'
        )

    def sendtcp(self, msg):
        # Check if msg is bytes:
        if type(msg) is not bytes:
            logging.error('sendTcp: msg is not bytes')
            sys.exit(1)
        # length of whole packet = length of sequence + length of msg
        payloadLen = 4 + len(msg)
        # noinspection PyBroadException
        try:
            self.tcpSock.send(struct.pack(
                '!II', payloadLen, self.sequence) + msg
            )
        except:
            self.tcpConnected = False
            self.selectLoopRunning = False
            self.emitList.append(
                {
                    'state': 'serverDisconnected'
                }
            )
        self.sequence += 1

    def sendudp(self, msg, address):
        # noinspection PyBroadException
        try:
            self.udpSock.sendto(msg, address)
        except:
            pass

    def sendHelp(self):
        logging.info('Sending help message')
        returnMessage = '!fcreplay record <challenge>, Eg: "!fcreplay record challenge-1111-1234567890.12@sfiii3n". !fcreplay status <challenge>. ' \
            'I can only record replays that show up on your profile page. ' \
            'Replays will be uploaded to https://www.youtube.com/channel/UCrYudzO9Nceu6mVBnFN6haA and https://fba-recorder.uc.r.appspot.com/'
        self.sendChat(returnMessage)

    def sendRecord(self, fcreplayCommands, profile):
        logging.info('Got a record request')

        if fcreplayCommands[2].endswith('sfiii3n'):
            challenge = fcreplayCommands[2]
            # Need to return message with status
            try:
                status = getfcplayerreplay(profile, challenge)
            except Exception as e:
                status = 'EXCEPTION'

            if status == 'ADDED' or status == 'MARKED_PLAYER':
                returnMessage = f"Hi @{profile}, I've added your replay to the encoding queue"
                # TODO return queue position
                self.sendChat(returnMessage)
            elif status == 'TOO_SHORT':
                returnMessage = f"Sorry @{profile}, the replay needs to be 60 seconds or longer"
                self.sendChat(returnMessage)
            elif status == 'ALREADY_EXISTS':
                returnMessage = f"Sorry @{profile}, the replay already exists"
                self.sendChat(returnMessage)
            elif status == 'EXCEPTION':
                returnMessage = f"Sorry @{profile}, there was something wrong with that request"
                self.sendChat(returnMessage)
        else:
            logging.info('Not a sfiii3n request')
            returnMessage = f"Sorry @{profile}, I can only record sfiii3n replays"
            self.sendChat(returnMessage)

    def sendStatus(self, fcreplayCommands, profile):
        logging.info('Got a status request')
        if len(fcreplayCommands) == 2:
            jobdata = fcjobstatus.get_current_job_details()
            remaning_time = fcjobstatus.get_current_job_remaining()

            returnMessage = f"@{profile} Currently encoding: '{jobdata.p1} vs {jobdata.p2}, {remaning_time}s remaining, the current job status is: {jobdata.status}"
            self.sendChat(returnMessage)

        elif fcreplayCommands[2].endswith('sfiii3n'):
            # Need to check if challenge is valid. Can't do until replay browser is fixed
            # Check to see if replay is finished:
            status = fcjobstatus.check_if_finished(fcreplayCommands[2])
            if status == 'FINISHED':
                challenge_replaced = fcreplayCommands[2].replace('@', '-')
                returnMessage = f"@{profile} That replay has finished being recorded. You can find it here: https://www.youtube.com/channel/UCrYudzO9Nceu6mVBnFN6haA"
            elif status == 'NO_DATA':
                returnMessage = f"@{profile} That replay doesn't exist in the queue"
            else:
                # Get position in queue
                position = fcjobstatus.get_queue_position(fcreplayCommands[2])
                # Get state of recording if currently recording
                if position == 0:
                    jobdata = fcjobstatus.get_current_job_details()
                    remaning_time = fcjobstatus.get_current_job_remaining()
                    returnMessage = f"@{profile} Currently recording that replay, {remaning_time}s remaining, the current job status is: {jobdata.status}"
                elif str(position) == 'NOT_PLAYER_REPLAY':
                    returnMessage = f"@{profile} That replay isn't a player replay, A player in that match will have to request to record it, " \
                        "or it will eventually be recorded when the queue is empty"
                else:
                    returnMessage = f"@{profile} Replay {fcreplayCommands[2]} is number {position} in the queue"
            self.sendChat(returnMessage)

    def sendAdvertise(self):
        if (int(time.time()) - self.advertiseTimeSent) > 3600:
            logging.info("Sending channel advertisement")
            returnMessage = "Use !fcreplay to upload your fightcade replays to youtube"
            self.sendChat(returnMessage)
            self.advertiseTimeSent = time.time()

    def emitLoop(self):
        # loop over events
        while True:
            # Send channel advertisement every hour
            self.sendAdvertise()

            try:
                emit = self.emitList.pop(0)
                logging.debug(f'Got Emit: {emit}')
            except IndexError as e:
                continue
            except Exception as e:
                logging.error(f'Unknown emit error: e')

            # Respond to !fcreplay messages
            if str(emit['state']) == 'chatReceived':
                # Don't capture my own messages lol
                if str(emit['name']) == 'fcreplay_bot':
                    continue

                if str(emit['message']).startswith('!fcreplay'):
                    logging.info(f"Receive bot command line {emit['message']}")
                    fcreplayCommands = str(emit['message']).split()
                    logging.info(
                        f'Split fcreplay commands received are: {fcreplayCommands}, length: {len(fcreplayCommands)}'
                    )

                    profile = emit['name']

                    if len(fcreplayCommands) == 1:
                        self.sendHelp()

                    elif len(fcreplayCommands) == 2:
                        if 'status' in fcreplayCommands[1]:
                            self.sendStatus(fcreplayCommands, profile)
                        else:
                            self.sendHelp()

                    elif len(fcreplayCommands) == 3:
                        if fcreplayCommands[1] == 'record':
                            self.sendRecord(fcreplayCommands, profile)
                        elif fcreplayCommands[1] == 'status':
                            self.sendStatus(fcreplayCommands, profile)
                        else:
                            self.sendHelp()

                    else:
                        self.sendHelp()


def main():
    c = Controller()
    c.tcpConnected = c.connectTcp()

    # Start loop in thread
    t = Thread(target=c.selectLoop)
    t.start()

    # Start emit loop in thread
    emitThread = Thread(target=c.emitLoop)
    emitThread.start()

    username = config['username']
    password = config['password']
    channel = config['channel']
    c.sendWelcome()
    c.sendAuth(username, password)

    c.sendListChannels()

    while True:
        if c.stateChannelIsLoaded:
            c.sendJoinChannelRequest(channel=channel)
            break

    logging.info('Joined channel and awaiting commands!')


if __name__ == '__main__':
    main()
