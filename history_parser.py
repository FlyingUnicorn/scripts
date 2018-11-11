import os
import sys
import re
import time

HLCLR='\033[1;93m'   # Yellow
INFOCLR='\033[44m'
NC="\033[0m"         # Color Reset

lst_timestamps = [(60, "< 1 min"),
                  (120, "< 2 min"),
                  (300,  "< 5 min"),
                  (600, "< 10 min"),
                  (1800, "< 30 min"),
                  (3600, "< 1 hr"),
                  (2*3600, "< 2 hr"),
                  (5*3600, "< 5 hr"),
                  (10*3600, "< 10 hr"),
                  (24*3600, "today"),
                  (48*3600, "yesterday")]

def find(path, pattern):
  if not path.strip() or not pattern.strip() or pattern.strip() == "''":
    sys.exit(-1)

  if pattern[0] == "'":
    pattern = pattern[1:]
  if pattern[-1] == "'":
    pattern = pattern[:-1]

  dct = {}
  with open(path) as f:
    lines = f.readlines()
    cmd_time_stamp = 0
    for indx, ln in enumerate(lines[:-1]):
      if ln[0] == '#':
        try:
          cmd_time_stamp = int(ln[1:])
        except ValueError:
          cmd_time_stamp = 0
      else:
        ln = ln.strip().lower()
        pattern = pattern.lower()

        if pattern in ln:
          if ln in dct:
            cnt = dct[ln][0]+1  # update counter
          else:
            cnt = 1
          dct[ln] = [cnt, indx, cmd_time_stamp] # save index of first encounter

  if not dct:
   # print('No matches for "{}"'.format(pattern))
    sys.exit(-2)

  maxcnt = 0
  maxfenc = 0
  len_maxts = 0
  lst_sorted_dct = sorted(dct.items(), key=lambda x: x[1][2])
  for n in range(len(lst_sorted_dct)):
    _, (cnt, first_enc, last_call) = lst_sorted_dct[n]
    maxcnt = max(maxcnt, cnt)
    maxfenc = max(maxfenc, first_enc)
    if last_call == 0:
      ts = " -- "
    else:
      try:
        since = int(time.time()) - last_call
        for t, p in lst_timestamps:
          if since < t:
            ts = p
            break
        else:
          ts = time.strftime('%Y-%m-%d', time.localtime(last_call))
      except TypeError:
        ts = " -- "
    lst_sorted_dct[n][1][2] = ts
    len_maxts = max(len_maxts, len(ts))

  len_maxcnt = len(str(maxcnt))
  len_maxfenc = len(str(maxfenc))

  for ln, (cnt, first_enc, ts) in lst_sorted_dct:
    clr_pattern = '{}{}{}'.format(HLCLR, pattern, NC)
    lnsplit = re.split(pattern, ln)

    if cnt > 1:
      print('{}[{:{}} ({:{}}) {:>{}}]{} '.format(INFOCLR, first_enc, len_maxfenc, cnt, len_maxcnt, ts, len_maxts, NC), end='')
    else:
      print('{}[{:{}} {} {:>{}}]{} '.format(INFOCLR, first_enc, len_maxfenc, ' '*(len_maxcnt+2), ts, len_maxts, NC), end='')

    if lnsplit[0]:
      print(lnsplit[0], end='')
    print(clr_pattern, end='')

    for n in lnsplit[1:-1]:
      print(n, end='')
      print(clr_pattern, end='')

    if lnsplit[-1]:
      print(lnsplit[-1], end='')
    print()

def get(path, line_num):
  try:
    line_num_p = int(line_num.lstrip().rstrip())
  except ValueError:
    print("Value not an integer [{}]".format(line_num))
    sys.exit(-1)

  with open(path) as f:
    for indx, ln in enumerate(f):
      if indx == line_num_p:
        #print(ln.strip())
        sys.exit(ln.strip())
      else:
        pass

if __name__ == '__main__':
  if sys.argv[1] == '-find' and len(sys.argv) == 4:
    find(path=sys.argv[2], pattern=sys.argv[3])
  elif sys.argv[1] == '-get' and len(sys.argv) == 4:
    get(path=sys.argv[2], line_num=sys.argv[3])
  else:
    #find(path='/home/{}/.bash_history'.format(os.environ['USER']), pattern=sys.argv[1])
    #get(path='/home/{}/.bash_history'.format(os.environ['USER']), line_num=sys.argv[2])
    sys.exit(-1)
