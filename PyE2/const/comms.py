# -*- coding: utf-8 -*-
"""
Copyright 2019-2022 Lummetry.AI (Knowledge Investment Group SRL). All Rights Reserved.


* NOTICE:  All information contained herein is, and remains
* the property of Knowledge Investment Group SRL.  
* The intellectual and technical concepts contained
* herein are proprietary to Knowledge Investment Group SRL
* and may be covered by Romanian and Foreign Patents,
* patents in process, and are protected by trade secret or copyright law.
* Dissemination of this information or reproduction of this material
* is strictly forbidden unless prior written permission is obtained
* from Knowledge Investment Group SRL.


@copyright: Lummetry.AI
@author: Lummetry.AI - AID
@project: 
@description:
Created on Sat Jan 28 13:01:28 2023
"""

from . import base as BASE_CT

SB_ID = BASE_CT.SB_ID
EE_ID = BASE_CT.EE_ID

HOST = 'HOST'
TOPIC = 'TOPIC'
BROKER = 'BROKER'
PORT = 'PORT'
USER = 'USER'
PASS = 'PASS'
VHOST = 'VHOST'
DEVICE_ID = 'DEVICE_ID'
ROUTING_KEY = 'ROUTING_KEY'
QOS = 'QOS'

EXCHANGE = 'EXCHANGE'
EXCHANGE_TYPE = 'EXCHANGE_TYPE'
QUEUE = 'QUEUE'
QUEUE_DURABLE = 'QUEUE_DURABLE'
QUEUE_EXCLUSIVE = 'QUEUE_EXCLUSIVE'
QUEUE_DEVICE_SPECIFIC = 'QUEUE_DEVICE_SPECIFIC'

COMMUNICATION_CONFIG_CHANNEL = 'CONFIG_CHANNEL'
COMMUNICATION_PAYLOADS_CHANNEL = 'PAYLOADS_CHANNEL'
COMMUNICATION_CTRL_CHANNEL = 'CTRL_CHANNEL'
COMMUNICATION_NOTIF_CHANNEL = 'NOTIF_CHANNEL'
COMMUNICATION_VALID_CHANNELS = [
    COMMUNICATION_CONFIG_CHANNEL, COMMUNICATION_PAYLOADS_CHANNEL,
    COMMUNICATION_CTRL_CHANNEL, COMMUNICATION_NOTIF_CHANNEL
]
COMMUNICATION_DEFAULT = 'DEFAULT'
COMMUNICATION_COMMAND_AND_CONTROL = 'COMMANDCONTROL'
COMMUNICATION_HEARTBEATS = 'HEARTBEATS'
COMMUNICATION_NOTIFICATIONS = 'NOTIFICATIONS'
COMMUNICATION_VALID_TYPES = [
    COMMUNICATION_DEFAULT, COMMUNICATION_COMMAND_AND_CONTROL,
    COMMUNICATION_HEARTBEATS, COMMUNICATION_NOTIFICATIONS
]
