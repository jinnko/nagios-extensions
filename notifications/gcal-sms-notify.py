#!/usr/bin/env python
#
# @author jinnko
# @since 2011-02-14
# @version $Id: $
#
# DISCLAIMER: Doesn't always work perfectly.  The event is added on the 
# DISCLAIMER: calendar but the SMS doesn't always arrive.   Use at your own risk!!!!!
#
# Test this script by running something like this:
#  NAGIOS_SERVICEDESC=clitest NAGIOS_SERVICESTATE=up NAGIOS_SERVICEOUTPUT=someOutput NAGIOS_NOTIFICATIONTYPE=warning NAGIOS_SHORTDATETIME=now NAGIOS_HOSTNAME=hostname NAGIOS_HOSTSTATE=up NAGIOS_HOSTOUTPUT=allGood ./gcal-sms-notify.py
#
###
# Configurables
###
cal["email"] = 'email@gmail.com'
cal["password"] = 'password'
cal["id"] = 'gmail_calendar_id'

###
# No touchy after here unless you know what you're doing
###
import gdata.calendar.service
import gdata.calendar
import atom
import time
from os import getenv

cal_service = gdata.calendar.service.CalendarService()
cal_service.email = cal["email"]
cal_service.password = cal["password"]
cal_service.source = 'Google-Calendar_Python_Sample-1.0'
cal_service.ProgrammaticLogin()

def InsertSingleEvent(calendar_service, title='Opsview generated default event',
                      content='This is a default generated event by Opsview', where='',
                      start_time=None, end_time=None, reminder=None):
    event = gdata.calendar.CalendarEventEntry()
    event.title = atom.Title(text=title)
    event.content = atom.Content(text=content)
    event.where.append(gdata.calendar.Where(value_string=where))

    if start_time is None:
      # Use current time for the start_time and have the event last 5 mins
      start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() + (6*60)))
      end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() + 1800))
    when = gdata.calendar.When(start_time=start_time, end_time=end_time)

    if reminder is None:
        reminder = gdata.calendar.Reminder(minutes=5, extension_attributes={"method":"sms"})
        when.reminder.append(reminder)

    event.when.append(when)

    # Use the Calendar ID to insert into a secondary calendar, otherwise use 'default'
    cal_id = cal["id"]
    new_event = calendar_service.InsertEvent(event, '/calendar/feeds/'+cal_id+'/private/full')

    print 'New single event inserted: %s' % (new_event.id.text,)
    print '\tEvent edit URL: %s' % (new_event.GetEditLink().href,)
    print '\tEvent HTML URL: %s' % (new_event.GetHtmlLink().href,)

    return new_event

def GetNagiosEnv():
    data = {
        'service_desc': getenv('NAGIOS_SERVICEDESC'),
        'service_state': getenv('NAGIOS_SERVICESTATE'),
        'service_output': getenv('NAGIOS_SERVICEOUTPUT'),
        'notification_type': getenv('NAGIOS_NOTIFICATIONTYPE'),
        'notification_datetime': getenv('NAGIOS_SHORTDATETIME'),
        'notification_hostname': getenv('NAGIOS_HOSTNAME'),
        'notification_hoststate': getenv('NAGIOS_HOSTSTATE'),
        'notification_hostoutput': getenv('NAGIOS_HOSTOUTPUT'),
    }
    return data

def NotifyUser():
    data = GetNagiosEnv()

    if data['service_desc']:
        text = "%s: %s on %s is %s: %s (%s)" % (data['notification_type'], data['service_desc'], data['notification_hostname'], data['service_state'], data['service_output'], data['notification_datetime'])

    else:
        text = "%s: %s is %s: %s (%s)" % (data['notification_type'], data['notification_hostname'], data['notification_hoststate'], data['notification_hostoutput'], data['notification_datetime'])

    print "Sending notification: %s" % text
    InsertSingleEvent(cal_service, title=text, content=text)

NotifyUser()
