#!/bin/sh
neuro --network-timeout=600 acl list --shared | awk '{print "neuro acl revoke "$1" "$3}' | sh
