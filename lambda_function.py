# -*- coding: utf-8 -*-

from ec2_scheduler import EC2Scheduler

def lambda_handler(event, context):
    access_id = 'AWS AccessID'
    secret_key = 'AWS SecretKey'
    conf = 'schedule.cfg'

    schedule = EC2Scheduler(access_id=access_id, secret_key=secret_key, conf=conf)
    schedule.job()

