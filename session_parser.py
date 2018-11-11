import sys
import os
import time
from datetime import datetime, timedelta

str_project_entry = '<project>'
str_session_entry = '<session>'

fmt_timestamp = '%Y-%m-%d_%H:%M'
fmt_timestamp_date = '%Y-%m-%d'
fmt_timestamp_time = '%H:%M'

class Session:
  def __init__(self, start=None, end=None):

    if not start:
      self.start = datetime.now()
    else:
      self.start = datetime.strptime(start, fmt_timestamp)

    if not end:
      self.end = None
    else:
      self.end = datetime.strptime(end, fmt_timestamp)

  def end_session(self):
    self.end = datetime.now()

  def __str__(self):
    str_fmt = '{} {}'.format(fmt_date(self.start), fmt_time(self.start))
    if self.end:
      str_fmt += '-{}'.format(fmt_time(self.end))
      str_fmt += ' duration: {}'.format(fmt_dur(self.dur()))
    return str_fmt

  def dur(self):
    if self.end:
      return self.end-self.start
    else:
      return 0

    
  def formatted(self):
    str_fmt = '{}'.format(self.start.strftime(fmt_timestamp))
    if self.end:
      str_fmt += ' {}'.format(self.end.strftime(fmt_timestamp))
    return str_fmt

  
class Project:
  def __init__(self, name):
    self.name = name
    self.lst_sessions = []
    self.session_ongoing = False

  def __str__(self):
    return 'Project: {}'.format(self.name)

  def start_session(self):
    self.lst_sessions.append(Session())

  def end_session(self):
    self.lst_sessions[-1].end_session()

  def formatted_sessions(self):
    str_fmt = ''
    for s in self.lst_sessions:
      str_fmt += '{}{} {}\n'.format(str_session_entry, self.name, s.formatted())
    return str_fmt

  def check_ongoing(self):
    for s in self.lst_sessions:
      if s.end == None:
        if self.session_ongoing:
          print("More than one ungoing session!")
          sys.exit(-1)
        self.session_ongoing = True

  def info(self):
    str_info = ''
    str_info += 'Project: {}   ongoing: {}\n'.format(self.name, self.session_ongoing)
    for s in self.lst_sessions:
      str_info += str(s) + '\n'
    return str_info

class SessionDB:
  def __init__(self, path):
    self.path = path
    self.dct_projects = {}

    for ln in open(self.path):
      ln = ln.strip()
      if str_project_entry == ln[:len(str_project_entry)]:
        projname = ln.split(str_project_entry)[1]
        self.dct_projects[projname] = Project(projname)

      if str_session_entry == ln[:len(str_session_entry)]:
        ln_session = ln.split(str_session_entry)[1]
        fields = ln_session.split()
        projname = fields[0]
        if len(fields) == 3:
          session = Session(start=fields[1], end=fields[2])
        else:
          session = Session(start=fields[1])
        self.dct_projects[projname].lst_sessions.append(session)

    for p in self.dct_projects.values():
      p.check_ongoing()

  def close(self):
    with open(self.path, 'w') as fout:
      for p in self.dct_projects.values():
        print('<project>{}'.format(p.name), file=fout)
        print(p.formatted_sessions(), file=fout)

  def add_project(self, projname):
    if projname in self.dct_projects:
      print('Project already in DB')
      sys.exit(-1) # exit without updating db

    self.dct_projects[projname] = Project(projname)

  def start_session(self, projname):
    if not projname in self.dct_projects:
      print('Invalid project: {}'.format(projname))
      sys.exit(-1)

    if self.dct_projects[projname].session_ongoing:
      print('Session already started')
      sys.exit(-1) # exit without updating db
    self.dct_projects[projname].start_session()

  def end_session(self, projname):
    if not projname in self.dct_projects:
      print('Invalid project: {}'.format(projname))
      sys.exit(-1) # exit without updating db

    if not self.dct_projects[projname].session_ongoing:
      print('Session not started')
      sys.exit(-1) # exit without updating db

    self.dct_projects[projname].end_session()

  def info(self):
    for p in self.dct_projects.values():
      print(p.info())

  def stats(self, week=None):
    dct_date = {}

    if week:
      d_start=datetime.strptime('{}-{}'.format(datetime.now().year, week) + '-1', "%Y-%W-%w")
      d_end=d_start+timedelta(days=7)
    else:
      d_start=None
      d_end=None
    for p in self.dct_projects.values():
      for s in p.lst_sessions:
        date = '{:04}-{:02}-{:02}'.format(s.start.year, s.start.month, s.start.day)
        if date in dct_date:
          dct_date[date].append(s)
        else:
          dct_date[date] = [s]

    total_dur = timedelta()
    for date, lst_sessions in dct_date.items():

      date=datetime.strptime(date, fmt_timestamp_date)
      if d_start and date < d_start:
        continue
      if d_end and date > d_end:
        continue

      str_ongoing = ''
      total_dur_day = timedelta()
      str_day = ''
      for s in lst_sessions:
        if not s.end:
          str_ongoing = '(ongoing)'
          end = datetime.now()
        else:
          end = s.end
        str_day += '\t{}-{} {} {}\n'.format(fmt_time(s.start), fmt_time(end), fmt_dur(end-s.start), str_ongoing)
        total_dur_day += end-s.start
      print('Date: {}\n\tDuration: {}'.format(fmt_date(date), fmt_dur(total_dur_day)))
      print(str_day)
      total_dur += total_dur_day

    if week:
      print('Week: {}'.format(week))
    print('Total dur: {} {}'.format(fmt_dur(total_dur), str_ongoing))

####################
# Helper Functions #
####################
def fmt_dur(dur):
  # dur in timedelta format      print(total_dur_day, total_dur)
  return '{:2}:{:02}'.format(int(dur.total_seconds() / 3600), int((dur.total_seconds() % 3600) / 60))

def fmt_date(date):
  # date in datetime format
  return date.strftime(fmt_timestamp_date)

def fmt_time(time):
  return time.strftime(fmt_timestamp_time)

########
# Main #
########
if __name__ == '__main__':
  path_db='/home/jonas/time_db.txt'
  db = SessionDB(path=path_db)
  if len(sys.argv) == 2 and sys.argv[1] == '-info':
    db.info()
  elif len(sys.argv) == 3 and sys.argv[1] == '-new-project':
    db.add_project(sys.argv[2])
  elif len(sys.argv) == 3 and sys.argv[1] == '-start-session':
    db.start_session(sys.argv[2])
  elif len(sys.argv) == 3 and sys.argv[1] == '-end-session':
    db.end_session(sys.argv[2])
  elif len(sys.argv) >= 2 and sys.argv[1] == '-stats':
    if len(sys.argv) == 3 and '-w' in sys.argv[2]:
      weeknum=int(sys.argv[2].split('-w')[1])
      db.stats(week=weeknum)
    elif len(sys.argv) == 2:
      db.stats()
    else:
      print('invalid argument')
      sys.exit(-1) # exit without updating db
  else:
    print('invalid argument {} {}'.format(len(sys.argv), sys.argv))
    sys.exit(-1) # exit without updating db
  db.close()
