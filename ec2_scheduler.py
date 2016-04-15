# -*- coding: utf-8 -*-

import time, ConfigParser
from datetime import datetime
import pytz
import boto.ec2
 
class EC2Scheduler():
    """EC2Scheduler EC2インスタンスのスケジュール実行

    このクラスはAWS EC2インスタンスの起動・停止をスケジュール実行が行えます。

    スケジュール実行するには、設定ファイル(例: schedule.cfg)が予め必要なります。

    Example:
        [Develop]
        region: ap-northeast-1 <= リージョン
        type: daily <= 実行Type
        tag-key: AWS-Schedule <= インスタンスタグ名
        tag-value: Dev-Weekday <= タグ値
        start: 9:00 <= 起動
        stop: 21:00 <= 停止
        skip: saturday, sunday <= スキップする日を曜日で指定
        timezone: Asia/Tokyo <= タイムゾーン指定


    設定ファイルを作成後、AWSアクセスに必要なAccessID, SecretKeyを用意し実行します。

    Example:
        from ec2_scheduler import EC2Scheduler

        access_id = 'AWS AccessID'
        secret_key = 'AWS SecretKey'
        conf = 'schedule.cfg'

        schedule = EC2Scheduler(access_id=access_id, secret_key=secret_key, conf=conf)
        schedule.job()
    """
 
    week = {
        'monday':0,
        'tuesday':1,
        'wednesday':2,
        'thursday':3,
        'friday':4,
        'saturday':5,
        'sunday':6
    }

    run_stat = [80]
    stop_stat = [16]

    def __getattr__(self, arg):
        raise AttributeError('Attribute %r not found' % (arg,))


    def __init__(self, access_id=None, secret_key=None, conf=None):
        """
        Args:
            access_id: AWS AccessID
            secret_key: AWS SecretKey
            conf: Config File
        """
        self._access_id = access_id
        self._secret_key = secret_key
        self.conf_file = conf

        self.config()


    def config(self):
        """
        ConfigParser初期化
        設定ファイル読込
        """
        self.conf = ConfigParser.SafeConfigParser()
        self.conf.read(self.conf_file)


    def job(self):
        """
        設定毎にジョブを実行
        """
        for section in self.conf.sections():
            self.section = section
            getattr(self, self.get_param('type'))()


    def daily(self):
        """
        日毎のスケジュール実行処理
        """
        tz = pytz.timezone(self.get_param('timezone'))

        """
        設定ファイルの時間から、今日の日時をUnixTimeで作る
        """
        start = self.mk_datetime(tz, self.get_param('start'))
        stop = self.mk_datetime(tz, self.get_param('stop'))

        """
        現在日時をUnixTimeで取得
        """
        now = self.convert_unixtime(self.convert_currenttime(tz))

        """
         現在日時から、start or stopを算出する
         設定ファイルのskipに飛ばしたい曜日の指定があれば、それも合わせる
        """
        actionStatus = self.switch_action(start, stop, now) & self.skip_weekday(tz)

        """
        start or stop
        """
        self.action(actionStatus)


    def action(self, status):
        """
        タグに紐付いたインスタンスを起動・停止する
        """
        try:
            con = boto.ec2.connect_to_region(
                aws_access_key_id=self._access_id,
                aws_secret_access_key=self._secret_key,
                region_name=self.get_param('region'))

            reservations = con.get_all_instances(filters={
                'tag-key':self.get_param('tag-key'),
                'tag-value':self.get_param('tag-value')})

            ec2_instances = [instance for reservation in reservations for instance in reservation.instances]

            for ec2_instance in ec2_instances:
                print('EC2 instance {} {}'.format(ec2_instance.id, ec2_instance.instance_type))
                if status:
                    """
                    サーバが停止状態(stopped)なら起動
                    """
                    if ec2_instance.state_code in self.run_stat:
                        ec2_instance.start()
                        print('Start the instance: {} {}'.format(ec2_instance.id, ec2_instance.instance_type))
                else:
                    """
                    サーバが稼働状態(running)なら停止
                    """
                    if ec2_instance.state_code in self.stop_stat:
                        ec2_instance.stop()
                        print('Stop the instance: {} {}'.format(ec2_instance.id, ec2_instance.instance_type))

        except:
            print('EC2 Access Error')


    def get_param(self, key):
        """
        設定ファイルからパラメータのValueを取り出す
        複数のValueを取得場合、カンマ区切りでセパレート
        """
        param = [item for item in self.conf.get(self.section, key).replace(' ', '').split(',')]

        return param if len(param) > 1 else param[0]


    def mk_datetime(self, tz, up_time):
        """
        引数の時間から現在日時のUnixTimeに変換して返す
        """
        return self.convert_unixtime(self.convert_currenttime(tz, up_time))


    def convert_currenttime(self, tz, up_time = None):
        """
        引数のTimeZoneと時間に合わせた日時を、時間指定が無い場合、現在日時を返す
        """
        date_format = '%Y-%m-%d %H:%M:%S' if up_time is None else '%Y-%m-%d {time}:00'

        return datetime.now(tz).strftime(date_format.format(time=up_time))


    def convert_unixtime(self, str_time):
        """
        指定時刻(文字列)からUnixTimeへ変換
        """
        time_tuple =  datetime(*time.strptime(str_time, '%Y-%m-%d %H:%M:%S')[0:6]).timetuple()

        return int(time.mktime(time_tuple))


    def skip_weekday(self, tz):
        """
        スキップさせる曜日を取得
        今日の曜日を取得し、設定とマッチしていたらスキップさせる
        """
        return (datetime.now(tz).weekday() not in [self.week[day] for day in self.get_param('skip') if day in self.week])


    def switch_action(self, start, stop, now):
        """
        現在時刻の状態を取得し、サーバが稼働時間内なのか停止するのかをチェックする
        """
        return (now >= start and now < stop) if start < stop else not (now >= stop and now < start)

