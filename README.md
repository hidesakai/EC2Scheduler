AWS Lambda EC2 Schduler
===

Overview
EC2インスタンスをスケジュール起動・停止するAWS Lambda Function

## Description
AWS LambdaのSchedule eventを使い、EC2インスタンスを一括でスケジュール起動・停止するスクリプトです。

## Requirement
* Python2.7
* pip

依存するライブラリ
* [AWS SDK for Python](http://aws.amazon.com/jp/sdkforpython/)
* [pytz](https://pypi.python.org/pypi/pytz/)

## Install
```
pip install boto -t path/to/ec2_scheduler/
pip install pytz -t path/to/ec2_scheduler/
```

## How to use
schedule.py
```
[Develop]
region: ap-northeast-1
type: daily
tag-key: AWS-Schedule
tag-value: Dev-Weekday
start: 10:00
stop: 20:00
skip: saturday, sunday
timezone: Asia/Tokyo
```

lambda_function.py
```
from ec2_scheduler import EC2Scheduler

def lambda_handler(event, context):
    access_id = 'AWS AccessID'
    secret_key = 'AWS SecretKey'
    conf = 'schedule.cfg'

    schedule = EC2Scheduler(access_id=access_id, secret_key=secret_key, conf=conf)
    schedule.job()
```

ZIPへ圧縮してAWS Lambdaへアップロード
```
cd path/to/ec2_scheduler/
zip -r lambda_function.zip .
```
