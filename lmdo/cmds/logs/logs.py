from __future__ import print_function
import datetime
import time
import json
import os
import collections

from lmdo.cmds.aws_base import AWSBase
from lmdo.oprint import Oprint

class Logs(AWSBase):
    """Cloudwatch logs handler"""
    def __init__(self):
        super(Logs, self).__init__()
        self._client = self.get_client('logs') 
        self._wait = object()

    @property
    def client(self):
        return self._client

    def tail(self):
        """Tailing the log stream"""
        try:
            self.get_logs(tail=True)
        except KeyboardInterrupt:
            os._exit(0)

    def get_logs(self, tail=False):
        """Fetch cloudwatch logs"""
        if self._args.get('function'):
            function_name = self.get_lmdo_format_name(self._args.get('<function_name>'))
            log_group_name = '/aws/lambda/{}'.format(function_name)
        else:
            log_group_name = self._args.get('<log_group_name>')
       
        # Maximum cache number of log entry IDs
        max_search = 5000
        recent_log = collections.deque(maxlen=max_search)
        recent_log.appendleft(0)
        for event in self.generate_logs(log_group_name):
            if event is self._wait:
                if self._args.get('-f') or self._args.get('--follow'):
                    time.sleep(1)
                    continue
                else:
                    return True
                
            if event['eventId'] not in recent_log:
                if len(recent_log) == max_search:
                    recent_log.pop()

                recent_log.appendleft(event['eventId'])
                self.print_to_console(event)
            else:
                continue

    def generate_logs(self, log_group_name):
        """Log generator"""
        if not log_group_name:
            Oprint.err('No log group name given, exit...', 'logs')
 
        kw = {}
        kw['log_group_name'] = log_group_name
        kw['interleaved'] = True

        start_time = self.get_start_time()
        if start_time:
            kw['startTime'] = start_time

        end_time = self.get_end_time()
        if end_time:
            kw['endTime'] = end_time
        
        while True:
            try:
                response = self.filter_logs(**kw)
            except Exception as e:
                Oprint.err('No Cloudwatch logs found for {}'.format(log_group_name), 'logs')
            
            if response:
                for event in response.get('events'):
                    yield event

                if response.get('nextToken'):
                    kw['nextToken'] = response.get('nextToken')
                else:
                    yield self._wait
            
            else:
                Oprint.err('No Cloudwatch logs found for {}'.format(log_group_name), 'logs')

    def print_to_console(self, event):
        """Out put logs"""
        print('--------------------------------------------')
        print(event['message'])
        #Oprint.warn(event['message'], 'logs')

        return True

    def filter_logs(self, log_group_name, **kwargs): 
        """Get logs from cloudwatch logs"""
        limit = kwargs.pop('limit', 100)
        try:
            response = self._client.filter_log_events(logGroupName=log_group_name, limit=limit, **kwargs)
        except Exception as e:
            Oprint.warn(e, 'logs')
            return {}

        return response

    def get_start_time(self):
        """Get start time from input"""
        day = self._args.get('--day')
        start_date = self._args.get('--start-date')

        if day:
            return int((datetime.date.today() - datetime.timedelta(abs(int(day)))).strftime("%s")) * 1000

        if start_date:
            return self.str_to_milliseconds(start_date)

        return False

    def get_end_time(self):
        """Get end time from input"""
        end_date = self._args.get('--end-date')

        if end_date:
            return self.str_to_milliseconds(end_date)

        return False

    def str_to_milliseconds(self, value, t_format='%Y-%m-%d'):
        """Convert string date to milliseconds timestamp"""
        return int(datetime.datetime.strptime(value, t_format).strftime("%s")) * 1000


