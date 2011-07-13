#!/usr/bin/perl -w
#
# script for nagios notify via Jabber / Google Talk Instant Messaging
#   using XMPP protocol and SASL PLAIN authentication.
#
# author: Andrew Elwell <A.Elwell@physics.gla.ac.uk>
# based on work by Thus0 <Thus0@free.fr> and  David Cox
#
# released under the terms of the GNU General Public License v2
# Copyright 2007 Andrew Elwell.

use strict;
use Net::XMPP;

## Configuration
my $username = ""; # Part before the @ in your email address
my $password = "";
my $componentname = 'gmail.com'; # domain at google apps
my $resource = "nagios";
## End of configuration


# JHK - replace this with NAGIOS_CONTACTPAGER
#my $len = scalar @ARGV;
#if ($len ne 2) {
#   die "Usage...\n $0 [jabberid] [message]\n";
#}
#my @field=split(/,/,$ARGV[0]);
#------------------------------------

# Google Talk & Jabber parameters :

my $hostname = 'talk.google.com';
my $port = 5222;
my $connectiontype = 'tcpip';
my $tls = 1;

#------------------------------------
sub ldie { $_ = shift; print $_. $/; exit 1 }
my $field = $ENV{NAGIOS_CONTACTEMAIL} || ldie "Must have CONTACTEMAIL for this notification script";
my @field = split(/,/, $field);
my $text;
if ( $ENV{NAGIOS_SERVICEDESC} ) {
    $text = "$ENV{NAGIOS_NOTIFICATIONTYPE}: $ENV{NAGIOS_SERVICEDESC} on $ENV{NAGIOS_HOSTNAME} is $ENV{NAGIOS_SERVICESTATE}: $ENV{NAGIOS_SERVICEOUTPUT} ($ENV{NAGIOS_SHORTDATETIME})";
}
else {
    $text = "$ENV{NAGIOS_NOTIFICATIONTYPE}: $ENV{NAGIOS_HOSTNAME} is $ENV{NAGIOS_HOSTSTATE}: $ENV{NAGIOS_HOSTOUTPUT} ($ENV{NAGIOS_SHORTDATETIME})";
}


#------------------------------------

my $Connection = new Net::XMPP::Client();

# Connect to talk.google.com
my $status = $Connection->Connect(
       hostname => $hostname, port => $port,
       componentname => $componentname,
       connectiontype => $connectiontype, tls => $tls);

if (!(defined($status))) {
   print "ERROR:  XMPP connection failed.\n";
   print "        ($!)\n";
   exit(0);
}

# Change hostname
my $sid = $Connection->{SESSION}->{id};
$Connection->{STREAM}->{SIDS}->{$sid}->{hostname} = $componentname;

# Authenticate
my @result = $Connection->AuthSend(
   username => $username, password => $password,
   resource => $resource);

if ($result[0] ne "ok") {
   print "ERROR: Authorization failed: $result[0] - $result[1]\n";
   exit(0);
}

# Send messages
open(LOG, ">>/var/log/nagios/notification-jabber.log");
foreach ( @field ) {
    $Connection->MessageSend(
        to       => "$_", 
        resource => $resource,
        subject  => "Notification",
        type     => "chat",
        body     => $text
    );
    print LOG "To: $_; resource: $resource; body: $text\n";
}
close(LOG);
