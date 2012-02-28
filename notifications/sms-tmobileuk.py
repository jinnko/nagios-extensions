#!/usr/bin/python
#
# tmobile.py - send a web sms
#
# Usage: sms-tmobileuk.py
# Test in nagios with:
#   NAGIOS_CONTACTPAGER=12_DIGIT_NUMBER /usr/local/nagios/utils/test_notifications serviceproblem /usr/local/nagios/libexec/notifications/sms-tmobileuk.py

import os
import sys
import getopt
import urllib2
import cookielib
import ConfigParser
from urllib import urlencode
from BeautifulSoup import BeautifulSoup

def debugCookies(cj):
	print "=== debugCookies() =============================================================="
	for index, cookie in enumerate(cj):
		print index, '  :  ', cookie
	print "================================================================================="


def getConfig():
	HOME = os.environ['HOME']
	# Get the config
	if os.path.isfile(os.path.join(HOME,'.nagios-sms.conf')):
		config = ConfigParser.RawConfigParser()
		config.read(os.path.join(HOME,'.nagios-sms.conf'))
		return config
	else:
		print "Config file is missing: %s" % (os.path.join(HOME,'.nagios-sms.conf'))
		print "Create this file with the service login credentials as follows, then try again."
		print "   [tmobileuk]"
		print "   username = web_username"
		print "   password = web_password"
		sys.exit(1)


def getNagiosEnv():
	data = {
		'NAGIOS_SERVICEDESC': os.getenv('NAGIOS_SERVICEDESC'),
		'NAGIOS_SERVICESTATE': os.getenv('NAGIOS_SERVICESTATE'),
		'NAGIOS_SERVICEOUTPUT': os.getenv('NAGIOS_SERVICEOUTPUT'),
		'NAGIOS_NOTIFICATIONTYPE': os.getenv('NAGIOS_NOTIFICATIONTYPE'),
		'NAGIOS_SHORTDATETIME': os.getenv('NAGIOS_SHORTDATETIME'),
		'NAGIOS_HOSTNAME': os.getenv('NAGIOS_HOSTNAME'),
		'NAGIOS_HOSTSTATE': os.getenv('NAGIOS_HOSTSTATE'),
		'NAGIOS_HOSTOUTPUT': os.getenv('NAGIOS_HOSTOUTPUT'),
		'NAGIOS_CONTACTPAGER': os.getenv('NAGIOS_CONTACTPAGER'),
	}
	return data

def getOptions():
	options = {}
	# Handle input opts
	try:
		opts, args = getopt.getopt(sys.argv[1:], "dv", ["debug", "verbose"])
	except getopt.GetoptError, err:
		# print help information and exit:
		print "getOptions() exception: ", str(err) # will print something like "option -a not recognized"
		sys.exit(2)

	options['debug'] = False
	options['verbose'] = False
	for o, a in opts:
		if o in ("-d", "--debug"):
			options['debug'] = True
			options['verbose'] = True
		elif o in ("-v", "--verbose"):
			options['verbose'] = True
		else:
			assert False, "unhandled option: %s" % (o)

	return options


def validateRecipient(recipient):
	try:
		if len(recipient) == 12:
			pass
		elif len(recipient) == 11:
			recipient = recipient.replace('0', '44', 1)
		else:
			print "Unrecognized recipient number: %s.  The number is expected to be 12 chars with the country code." % (recipient)
			sys.exit(1)

		if options['verbose']: print "Recipient: %s" % (recipient)
		return recipient

	except Exception, e:
		print "validateRecipient() exception:", e
		sys.exit(1)


def constructMessage(data):
	if data['NAGIOS_NOTIFICATIONTYPE'] == 'ACKNOWLEDGEMENT':
		print 'Not sending acknowledgement: %s' % (data['NAGIOS_SERVICEDESC'])
		sys.exit(0)

	text = ''
	if data['NAGIOS_SERVICEDESC']:
		text = "%s: %s on %s is %s: %s (%s)" % (
				data['NAGIOS_NOTIFICATIONTYPE'],
				data['NAGIOS_SERVICEDESC'],
				data['NAGIOS_HOSTNAME'],
				data['NAGIOS_SERVICESTATE'],
				data['NAGIOS_SERVICEOUTPUT'],
				data['NAGIOS_SHORTDATETIME']
			)
	else:
		text = "%s: %s is %s: %s (%s)" % (
				data['NAGIOS_NOTIFICATIONTYPE'],
				data['NAGIOS_HOSTNAME'],
				data['NAGIOS_HOSTSTATE'],
				data['NAGIOS_HOSTOUTPUT'],
				data['NAGIOS_SHORTDATETIME']
			)

	try:
		if len(text) < 20:
			print "Error: message too short. %s" % (text)
			sys.exit(1)

		elif len(text) > 160:
			text = text[0:160]

		if options['verbose']: print "Message: %s" % (text)

	except Exception, e:
		print "Error:", e
		sys.exit(1)

	return text


if __name__ == "__main__":
	config = getConfig()
	nagios_data = getNagiosEnv()
	options = getOptions()
	recipient = validateRecipient(nagios_data['NAGIOS_CONTACTPAGER'])
	message = constructMessage(nagios_data)

	# Instance configuration
	URL = {}
	URL['login'] = 'https://www.t-mobile.co.uk/service/your-account/login/'
	URL['sendsms_prepare'] = 'https://www.t-mobile.co.uk/service/your-account/private/wgt/send-text-preparing/'
	URL['sendsms_process'] = 'https://www.t-mobile.co.uk/service/your-account/private/wgt/send-text-processing/'

	TX = {}
	TX['headers'] = {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
	TX['data'] = None

	# Local config variables
	COOKIEFILE = os.path.join(os.environ['HOME'], '.nagios-sms.tmobileuk.lwp')

	# Load any cookies we may have from previous requests
	cj = cookielib.LWPCookieJar()
	if os.path.isfile(COOKIEFILE):
		cj.load(COOKIEFILE, ignore_discard=True)

	# Check if we'r already logged in
	if options['debug']: debugCookies(cj)

	logged_in = False
	for index, cookie in enumerate(cj):
		if cookie.name == 'logged_in_mtm' and cookie.value == "true":
			logged_in = True

	# Build the handler chain to intercept the cookies we receive
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	urllib2.install_opener(opener)

	if not logged_in:
		if options['verbose']: print "Requesting Login:", URL['login']

		# Request our first URL to establish a session with the service
		req = urllib2.Request(URL['login'], None, TX['headers'])
		handle = urllib2.urlopen(req)

		if options['debug']: debugCookies(cj)

		# Prepare for login
		TX['data'] = {}
		soup = BeautifulSoup(handle.read())
		for inputTag in soup.findAll('input'):
			inputName = inputTag.get('name')
			if inputName == 'username':
				TX['data']['username'] = config.get('tmobileuk', 'username')

			elif inputName == 'password':
				TX['data']['password'] = config.get('tmobileuk', 'password')

			else:
				try:
					if inputTag.get('value') is None:
						TX['data'][inputName] = ''
					else:
						TX['data'][inputName] = inputTag.get('value')
				except Exception, e:
					print "Exception finding inputs:", e

		# Login
		req = urllib2.Request(URL['login'], urlencode(TX['data']), TX['headers'])
		handle = urllib2.urlopen(req)

		if options['debug']:
			soup = BeautifulSoup(handle.read())
			for inputTag in soup.findAll('input'):
				inputName = inputTag.get('name')
				print "DEBUG: %s = %s" % ( inputName, inputTag.get('value') )

		# Save the received cookies
		cj.save(COOKIEFILE, ignore_discard=True)

	logged_in = False
	for index, cookie in enumerate(cj):
		if cookie.name == "logged_in_mtm" and cookie.value == "true":
			logged_in = True

	if logged_in is False:
		print "FATAL: Failed to log into service.  Check debug output using -d to identify why."
		sys.exit(1)
	
	if options['verbose']: print "Preparing to send message:", URL['sendsms_prepare']

	# Get the struts TOKEN
	req = urllib2.Request(URL['sendsms_prepare'], None, TX['headers'])
	handle = urllib2.urlopen(req)

	if options['debug']: debugCookies(cj)

	if options['verbose']: print "Sending message:", URL['sendsms_process']

	TX['data'] = {}
	soup = BeautifulSoup(handle.read())
	for inputTag in soup.findAll('input'):
		if inputTag.get('name') == 'org.apache.struts.taglib.html.TOKEN':
			TX['data']['org.apache.struts.taglib.html.TOKEN'] = inputTag.get('value')

	# Check that we were able to get a valid TOKEN.
	# Not having this suggests the web-sms service is currently unavailable
	if not TX['data'].has_key('org.apache.struts.taglib.html.TOKEN'):
		print "FATAL: the web-sms service appears to currently be unavailable."
		sys.exit(1)

	TX['data']['message'] = message
	TX['data']['selectedRecipients'] = recipient
	TX['data']['WWWWWWWWWWWWWWW'] = "        "
	TX['data']['submit'] = 'Send'

	if options['debug']:
		print "POST HEADERS:", TX['headers']
		print "POST DATA:", TX['data']

	req = urllib2.Request(URL['sendsms_process'], urlencode(TX['data']), TX['headers'])
	handle = urllib2.urlopen(req)

	if options['debug']: print "Submission response:", handle.read()
