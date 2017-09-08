# -*- coding: utf-8 -*-

# This file is part of EventGhost.
# Copyright © 2005-2017 EventGhost Project <http://www.eventghost.org/>
#
# EventGhost is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with EventGhost. If not, see <http://www.gnu.org/licenses/>.


# noinspection PyUnresolvedReferences
import eg

eg.RegisterPlugin(
    name="Log 2 Syslog",
    author="topic2k ",
    version="0.0.1",
    kind="other",
    guid="{604E5D09-3B7A-47BC-A0E9-602C996649E8}",
    createMacrosOnAdd=False,
    canMultiLoad=False,
    icon=None,
    description="Forwards the contents of the log windw to a syslog server.",
    url="https://github.com/ProjectEG/plugin-Log2Syslog",
)

import logging  # NOQA
import time  # NOQA
from logging.handlers import SysLogHandler  # NOQA

import wx  # NOQA


class Text(eg.TranslatableStrings):
    server = "Syslog server"
    port = "Port"
    facility = "Facility"
    severity = "Priority"
    facility_0 = "kernel messages"
    facility_1 = "user-level messages"
    facility_2 = "mail system"
    facility_3 = "system daemons"
    facility_4 = "security/authorization messages"
    facility_5 = "messages generated internally by syslogd"
    facility_6 = "line printer subsystem"
    facility_7 = "network news subsystem"
    facility_8 = "UUCP subsystem"
    facility_9 = "clock daemon"
    facility_10 = "security/authorization messages"
    facility_11 = "FTP daemon"
    facility_12 = "NTP subsystem"
    facility_13 = "log audit"
    facility_14 = "log alert"
    facility_15 = "clock daemon (note 2)"
    facility_16 = "local use 0  (local0)"
    facility_17 = "local use 1  (local1)"
    facility_18 = "local use 2  (local2)"
    facility_19 = "local use 3  (local3)"
    facility_20 = "local use 4  (local4)"
    facility_21 = "local use 5  (local5)"
    facility_22 = "local use 6  (local6)"
    facility_23 = "local use 7  (local7)"
    severity_50 = "Critical: critical conditions"
    severity_40 = "Error: error conditions"
    severity_30 = "Warning: warning conditions"
    severity_20 = "Informational: informational messages"
    severity_10 = "Debug: debug-level messages"

FACILITIES = (
    Text.facility_0,
    Text.facility_1,
    Text.facility_2,
    Text.facility_3,
    Text.facility_4,
    Text.facility_5,
    Text.facility_6,
    Text.facility_7,
    Text.facility_8,
    Text.facility_9,
    Text.facility_10,
    Text.facility_11,
    Text.facility_12,
    Text.facility_13,
    Text.facility_14,
    Text.facility_15,
    Text.facility_16,
    Text.facility_17,
    Text.facility_18,
    Text.facility_19,
    Text.facility_20,
    Text.facility_21,
    Text.facility_22,
    Text.facility_23,
)
SEVERITIES = (
    Text.severity_10,
    Text.severity_20,
    Text.severity_30,
    Text.severity_40,
    Text.severity_50,
)


class Log2Syslog(eg.PluginBase):
    text = Text

    def __init__(self):
        self.syslog = None

    def __start__(
            self,
            server="localhost",
            port=514,
            facility=SysLogHandler.LOG_LOCAL0,
            severity=2
    ):
        self.server = server
        self.port = port
        self.syslog = LogListener(server, port, facility, (severity + 1) * 10)
        eg.log.AddLogListener(self.syslog)

    def __stop__(self):
        eg.log.RemoveLogListener(self.syslog)
        self.syslog.remove()

    def Configure(
            self,
            server="localhost",
            port=514,
            facility=SysLogHandler.LOG_LOCAL0,
            severity=2  # INFO level
    ):
        text = self.text
        panel = eg.ConfigPanel()
        server_lbl = panel.StaticText(text.server)
        port_lbl = panel.StaticText(text.port)
        server_txt = panel.TextCtrl(server)
        port_int = panel.SpinIntCtrl(port, min=1, max=65535)
        facility_lbl = panel.StaticText(text.facility)
        facility_chc = panel.Choice(facility, FACILITIES)
        severity_lbl = panel.StaticText(text.severity)
        severity_chc = panel.Choice(severity, SEVERITIES)

        panel.sizer.AddMany((
            (server_lbl,),
            (server_txt,),
            (port_lbl,),
            (port_int,),
            (facility_lbl,),
            (facility_chc,),
            (severity_lbl,),
            (severity_chc,),
        ))

        while panel.Affirmed():
            panel.SetResult(
                server_txt.GetValue(),
                port_int.GetValue(),
                facility_chc.GetSelection(),
                severity_chc.GetSelection()
            )


class LogListener:
    def __init__(
            self,
            server="localhost",
            port=514,
            facility=SysLogHandler.LOG_LOCAL0,
            severity=logging.INFO
    ):
        syslogd = self.syslogd = SysLogHandler(
            address=(server, port),
            facility=facility,
        )
        syslogd.setLevel(severity)
        logger = self.logger = logging.getLogger("EG2syslog")
        logger.addHandler(syslogd)
        logger.setLevel(severity)

    def WriteLine(self, line, icon, wRef, when, indent):
        MSG = u'\uFEFF'
        MSG += (indent * u'   ')
        MSG += line.encode('utf-8')
        STRUCTURED_DATA = u'[origin software="{}" swVersion="{}"]'.format(
            eg.APP_NAME, eg.Version.string
        )
        MSGID = u'Log2Syslog'
        PROCID = unicode(wx.GetProcessId())
        APP_NAME = unicode(eg.APP_NAME)
        HOSTNAME = unicode(wx.GetFullHostName())
        # t = time.gmtime(when)
        t = time.localtime(when)
        TIMESTAMP = unicode(time.strftime("%Y-%m-%dT%H:%M:%SZ", t))
        VERSION = u'1'  # the version of the syslog format
        # FACILITY = 16  # allowed values: 0-23
        # SEVERITY = 6  # allowed values: 0-7
        # PRIVAL = (FACILITY * 8) + SEVERITY
        # PRI = '<' + str(PRIVAL) + '>'  # PRI is automatically added before
        #                                  the message by SysLogHandler. So
        #                                  set it there (see __init__)

        HEADER = unicode(
            #  PRI + VERSION + ' ' + TIMESTAMP + ' ' + HOSTNAME + ' '
            u' '.join((VERSION, TIMESTAMP, HOSTNAME, APP_NAME, PROCID, MSGID))
        )
        SYSLOG_MSG = u' '.join((HEADER, STRUCTURED_DATA, MSG))
        self.logger.log(self.syslogd.level, unicode(SYSLOG_MSG))

    def remove(self):
        self.logger.removeHandler(self.syslogd)



'''
Syslog Message Format (RFC 5424, March 2009)
https://tools.ietf.org/html/rfc5424


      SYSLOG-MSG      = HEADER SP STRUCTURED-DATA [SP MSG]

      HEADER          = PRI VERSION SP TIMESTAMP SP HOSTNAME
                        SP APP-NAME SP PROCID SP MSGID
      PRI             = "<" PRIVAL ">"
      PRIVAL          = 1*3DIGIT ; range 0 .. 191
      VERSION         = NONZERO-DIGIT 0*2DIGIT
      HOSTNAME        = NILVALUE / 1*255PRINTUSASCII

      APP-NAME        = NILVALUE / 1*48PRINTUSASCII
      PROCID          = NILVALUE / 1*128PRINTUSASCII
      MSGID           = NILVALUE / 1*32PRINTUSASCII

      TIMESTAMP       = NILVALUE / FULL-DATE "T" FULL-TIME
      FULL-DATE       = DATE-FULLYEAR "-" DATE-MONTH "-" DATE-MDAY
      DATE-FULLYEAR   = 4DIGIT
      DATE-MONTH      = 2DIGIT  ; 01-12
      DATE-MDAY       = 2DIGIT  ; 01-28, 01-29, 01-30, 01-31 based on
                                ; month/year
      FULL-TIME       = PARTIAL-TIME TIME-OFFSET
      PARTIAL-TIME    = TIME-HOUR ":" TIME-MINUTE ":" TIME-SECOND
                        [TIME-SECFRAC]
      TIME-HOUR       = 2DIGIT  ; 00-23
      TIME-MINUTE     = 2DIGIT  ; 00-59
      TIME-SECOND     = 2DIGIT  ; 00-59
      TIME-SECFRAC    = "." 1*6DIGIT
      TIME-OFFSET     = "Z" / TIME-NUMOFFSET
      TIME-NUMOFFSET  = ("+" / "-") TIME-HOUR ":" TIME-MINUTE


      STRUCTURED-DATA = NILVALUE / 1*SD-ELEMENT
      SD-ELEMENT      = "[" SD-ID *(SP SD-PARAM) "]"
      SD-PARAM        = PARAM-NAME "=" %d34 PARAM-VALUE %d34
      SD-ID           = SD-NAME
      PARAM-NAME      = SD-NAME
      PARAM-VALUE     = UTF-8-STRING ; characters '"', '\' and
                                     ; ']' MUST be escaped.
      SD-NAME         = 1*32PRINTUSASCII
                        ; except '=', SP, ']', %d34 (")

      MSG             = MSG-ANY / MSG-UTF8
      MSG-ANY         = *OCTET ; not starting with BOM
      MSG-UTF8        = BOM UTF-8-STRING
      BOM             = %xEF.BB.BF


      UTF-8-STRING    = *OCTET ; UTF-8 string as specified
                        ; in RFC 3629

      OCTET           = %d00-255
      SP              = %d32
      PRINTUSASCII    = %d33-126
      NONZERO-DIGIT   = %d49-57
      DIGIT           = %d48 / NONZERO-DIGIT
      NILVALUE        = "-"

'''

'''
FACILITY codes:
 0      kernel messages
 1      user-level messages
 2      mail system
 3      system daemons
 4      security/authorization messages
 5      messages generated internally by syslogd
 6      line printer subsystem
 7      network news subsystem
 8      UUCP subsystem
 9      clock daemon
10      security/authorization messages
11      FTP daemon
12      NTP subsystem
13      log audit
14      log alert
15      clock daemon (note 2)
16      local use 0  (local0)
17      local use 1  (local1)
18      local use 2  (local2)
19      local use 3  (local3)
20      local use 4  (local4)
21      local use 5  (local5)
22      local use 6  (local6)
23      local use 7  (local7)
'''
'''
SEVERITY codes:
0       Emergency: system is unusable
1       Alert: action must be taken immediately
2       Critical: critical conditions
3       Error: error conditions
4       Warning: warning conditions
5       Notice: normal but significant condition
6       Informational: informational messages
7       Debug: debug-level messages
'''
'''
SD-ID's:
timeQuality: (tzKnown | isSynced | syncAccuracy ) = 0 | 1
origin: (ip | enterpriseId | software )
meta: (sequenceId | sysUpTime | language)
'''