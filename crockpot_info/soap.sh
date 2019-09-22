#!/bin/bash

if [ $# -eq 0 ]; then
    SERVICETYPE="urn:Belkin:service:basicevent:1"
    ACTION="GetCrockpotState"
    CONTROLURL="/upnp/control/basicevent1"
    HOST="192.168.1.123"
else
    SERVICETYPE=$1
    ACTION=$2
    CONTROLURL=$3
    HOST=$4
fi

DATA="<?xml version=\"1.0\"?>\
  <SOAP-ENV:Envelope \
    xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\" \
    SOAP-ENV:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\
      <SOAP-ENV:Body>\
          <m:$ACTION xmlns:m=\"$SERVICETYPE\"></m:$ACTION>\
      </SOAP-ENV:Body>\
  </SOAP-ENV:Envelope>"

curl  -H "Host: $HOST" \
      -H "Content-type: text/xml" \
      -H "SOAPACTION: \"$SERVICETYPE#$ACTION\"" \
      "http://$HOST:49153$CONTROLURL" --data "$DATA"

exit 0