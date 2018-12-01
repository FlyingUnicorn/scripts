
import os
import sys
import time
import math
from datetime import datetime, timedelta

FMT_TIMESTAMP = '%Y-%m-%d %H:%M'
FMT_TIMESTAMP_DATE = '%Y-%m-%d'
FMT_TIMESTAMP_HHMM = '%H:%M'

####################
# Helper Functions #
####################
def fmt_dur(dur):
  sign = ' ' if dur > 0 else '-'
  dur = abs(dur)
  return '{}{:02}:{:02}'.format(sign, int(dur / 60), dur % 60)

def fmt_date(date):
  # date in datetime format
  return date.strftime(FMT_TIMESTAMP_DATE)

def fmt_time_hhmm(ts):
  return ts.strftime(FMT_TIMESTAMP_HHMM)

def fmt_date_time_file(ts):
    return ts.strftime(FMT_TIMESTAMP)

class SessionEntryFormatted:
    def __init__(self, stype, project, start, start_msg=None, end=None, end_msg=None):
        self.stype = stype
        self.project = project
        self.start = start
        self.start_msg = start_msg
        self.end = end
        self.end_msg = end_msg

        if self.stype == 'n':
            # onoing
            self.end = datetime.now()
            self.end = self.end.replace(second=0, microsecond=0)
            self.end_msg = '<ongoing>'

        self.date = self.start.date()
        if self.stype in ['s', 'n']:
            self.start_hhmm = self.start.strftime(FMT_TIMESTAMP_HHMM)
            self.end_hhmm = self.end.strftime(FMT_TIMESTAMP_HHMM)
            self.str_st_end = '{}-{}'.format(self.start_hhmm, self.end_hhmm)
            self.duration_min = int((self.end - self.start).seconds / 60)
        else:
            self.duration_min = self.start.hour * 60 + self.start.minute
            if self.stype == 'sa':
                self.str_st_end = "<Added>"
            elif self.stype == 'sx':
                self.str_st_end = "<Excluded>"
                self.duration_min = self.duration_min * -1

        self.msg = ''
        if self.start_msg and self.end_msg:
            self.msg = '{} <|> {}'.format(self.start_msg, self.end_msg)
        elif self.start_msg:
            self.msg = self.start_msg
        elif self.end_msg:
            self.msg = self.end_msg

    def __str__(self):
        str_msg = ''
        if self.msg:
            str_msg = ' Comment: {}'.format(self.msg)
        return 'Project: {} Date: {} {:11} Duration: {}{}'.format(self.project, self.date, self.str_st_end, fmt_dur(self.duration_min), str_msg)

    def fmt_str(self):
        str_msg = ''
        if self.msg:
            str_msg = ' Comment: {}'.format(self.msg)
        return '{:11} Duration: {}{}'.format(self.str_st_end, fmt_dur(self.duration_min), str_msg)

class Sessions(list):
    def __init__(self):
        pass

    def print_fmt(self):
        for se in self:
            print(se.fmt_str_ext)

    def print_stats(self, filter_projects, filter_date, filter_detail_level):
        dct = self.filter_stats()

        total = 0
        dct_time_projects = {}

        d_start = None
        d_end = None
        if filter_date:
            if '-w' in filter_date:
                week = int(filter_date.split('-w')[1])
                d_start=datetime.strptime('{}-{}'.format(datetime.now().year, week) + '-1', "%Y-%W-%w")
                d_end=d_start+timedelta(days=7)

        for date, dct_project in sorted(dct.items()):

            # filter dates
            cmp_date = datetime.strptime(date, '%Y%m%d')
            if d_start and cmp_date < d_start:
                continue
            if d_end and cmp_date > d_end:
                continue

            print('Date: {}'.format(cmp_date.strftime('%Y-%m-%d <w-%W %A>')))
            total_project = 0
            for project, lst_filtered in sorted(dct_project.items()):
                if filter_projects and project not in filter_projects:
                    continue
                total_day = 0
                str_day = ''
                for se_filtered in lst_filtered:
                    str_day += ('    {}\n'.format(se_filtered.fmt_str()))
                    total_day += se_filtered.duration_min
                total_project += total_day

                if project not in dct_time_projects:
                    dct_time_projects[project] = total_day
                else:
                    dct_time_projects[project] += total_day

                ## Print day stats
                print('Total: {} >  Project: {}'.format(fmt_dur(total_day), project))
                if filter_detail_level >= 3:
                    print(str_day)
            total += total_project

        print('\n --- SUMMARY ---')
        for project, project_total in sorted(dct_time_projects.items()):
            print('Project <{}> total: {}'.format(project, fmt_dur(project_total)))
        print('Total: {}'.format(fmt_dur(total)))

    def filter_stats(self):
        dct_filtered = {}
        dct_t = {}
        for se in self:
            date = se.get_date()

            if date not in dct_t:
                dct_t[date] = {}

            if se.project not in dct_t[date]:
                dct_t[date][se.project] = [se]
            else:
                dct_t[date][se.project].append(se)

            if date not in dct_filtered:
                dct_filtered[date] = {}
            if se.project not in dct_filtered[date]:
                dct_filtered[date][se.project] = []

        for date, dct_project in sorted(dct_t.items()):
            for project, lst_se in sorted(dct_project.items()):
                tstart = None
                for se in lst_se:
                    if se.etype in ['sa', 'sx']:
                        dct_filtered[date][project].append(
                            SessionEntryFormatted(stype=se.etype,
                                                  project=project,
                                                  start=se.timestamp,
                                                  start_msg=se.msg))
                    elif se.etype == 'ss':
                        if tstart:
                            #print(tstart)
                            #print(se)
                            print('already ongoing session > exit')
                            sys.exit(-1)
                        tstart = se
                    elif se.etype == 'se':

                        if not tstart:
                            # started prev day
                            tstart = se.timestamp.replace(hour=0, minute=0)
                            dct_filtered[date][project].append(
                                SessionEntryFormatted(stype='s',
                                                      project=project,
                                                      start=tstart,
                                                      start_msg='<wrap>',
                                                      end=se.timestamp,
                                                      end_msg=se.msg))
                        else:
                            dct_filtered[date][project].append(
                                SessionEntryFormatted(stype='s',
                                                      project=project,
                                                      start=tstart.timestamp,
                                                      start_msg=tstart.msg,
                                                      end=se.timestamp,
                                                      end_msg=se.msg))
                        tstart = None
                    else:
                        print(se.fmt_str)
                        print('no session start found')
                        sys.exit(-1)

                if tstart:
                    if tstart.timestamp.date() == datetime.today().date():
                        dct_filtered[date][project].append(
                            SessionEntryFormatted(stype='n',
                                                  project=project,
                                                  start=tstart.timestamp,
                                                  start_msg=tstart.msg))
                    else:
                        tend = tstart.timestamp
                        tend = tend.replace(day=tstart.timestamp.day+1, hour=0, minute=0)
                        dct_filtered[date][project].append(
                            SessionEntryFormatted(stype='s',
                                                  project=project,
                                                  start=tstart.timestamp,
                                                  start_msg=tstart.msg,
                                                  end=tend,
                                                  end_msg='<wrap>'))

        return dct_filtered

    def save_file(self, path):

        with open(path, 'w') as fout:
            for se in self:
                print(se.file_formatted(), file=fout)

class SessionEntry:
    def __init__(self, project, etype, timestamp, msg):
        self.project = project
        self.etype = etype
        self.timestamp = timestamp
        self.msg = msg
        self.fmt_str = '{} {} {}'.format(self.project, self.timestamp, self.msg)
        fmt_msg = ''
        if self.msg:
            fmt_msg = 'message: {}'.format(self.msg)
        self.fmt_str_ext = 'Project: {} time: {} {}'.format(self.project, self.timestamp, fmt_msg)

    def get_date(self):
        return '{}{:02}{:02}'.format(self.timestamp.year, self.timestamp.month, self.timestamp.day)
    def file_formatted(self):
        return '{}|{}|{}|{}'.format(self.etype, self.project, fmt_date_time_file(self.timestamp), self.msg)

def parse_file(path):
    s = Sessions()
    for ln in open(path):
        ln=ln.strip()
        fields = ln.split('|')

        if fields[0] in ['ss', 'sa', 'se', 'sx']:

            project   = fields[1]
            timestamp = datetime.strptime(fields[2], FMT_TIMESTAMP)
            msg = ''
            if fields[3]:
                msg = fields[3]
            se = SessionEntry(project, fields[0], timestamp, msg)

            s.append(se)
    return s

if __name__ == '__main__':
    s = parse_file('test_dup.txt')

    if len(sys.argv) >= 2 and sys.argv[1] in ['ss', 'se', 'sa', 'sx']:
        project = sys.argv[2]
        timedelta = int(sys.argv[3])
        #if sys.argv[1] in ['ss', 'se', 'sa', 'sx']
        timestamp = datetime.now()
        if sys.argv[1] in ['sa', 'sx']:
          timestamp = timestamp.replace(hour=0,
                                        minute=0,
                                        second=0,
                                        microsecond=0)

        minute = timestamp.minute + timedelta
        hour = timestamp.hour + math.floor(minute / 60)
        day = timestamp.day + math.floor(hour / 24)
        hour %= 24
        minute %= 60
        timestamp = timestamp.replace(day=day,
                                        hour=hour,
                                        minute=minute,
                                        second=0,
                                        microsecond=0)
        msg = ''
        if len(sys.argv) >= 5:
            msg = ' '.join(sys.argv[4:])
        s.append(SessionEntry(project, sys.argv[1], timestamp, msg))
    elif len(sys.argv) >= 2 and (sys.argv[1] == 'sa' or sys.argv[1] == 'sx'):
        project = sys.argv[2]
        msg = ''
        if len(sys.argv) >= 5:
            msg = ' '.join(sys.argv[4:])
        s.append(SessionEntry(project, sys.argv[1], timestamp, msg))

    s.print_stats([], 0, 3)
    s.save_file('test_dup.txt')

