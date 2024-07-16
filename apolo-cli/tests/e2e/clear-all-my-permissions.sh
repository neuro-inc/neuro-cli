#!/bin/sh
apolo --network-timeout=600 acl list --shared | awk '{print "apolo acl revoke "$1" "$3}' | sh
