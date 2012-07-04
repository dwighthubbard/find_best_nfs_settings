#!/usr/bin/python
import tempfile,os,time,sys,optparse

DEBUG=False
STATUS=False

# Size of the test file in K bytes
TESTSIZE=8192
WSIZEMAX=32768
WSIZEMIN=1024
WSIZEINC=1024
RSIZEMAX=32768
RSIZEMIN=1024
RSIZEINC=1024

def findbestwsize(nfshost,nfsmountpoint,proto='udp',testsize=65535):
  speeds={0: 9999999.0}
  bestsize=0
  bestspeed=0
  #ddcount=16384
  ddcount=4096
  char='\0'
  block=''
  for i in range(0,1024):
    block=block+char
  mountpoint=tempfile.mkdtemp()
  for wsize in range(WSIZEMAX,WSIZEMIN-1,-WSIZEINC):
    if STATUS: print 'Testing',proto,'wsize of',wsize,
    os.system('mount -o wsize=%d,proto=%s %s:%s %s' % (wsize,proto,nfshost,nfsmountpoint,mountpoint))
    #line=os.popen('dd if=/dev/zero of=%s/%s bs=16k count=%d 2>&1|tail -1' % (mountpoint,'tempfile',ddcount),'r').readlines()[0].strip()
    #splitline=line.split(',')
    #speeds[wsize]=float(splitline[1].split()[0])
    starttime=time.time()
    file=open('%s/%s' % (mountpoint,'tempfile'),'w')
    for count in range(0,testsize):
      file.write(block)
    file.close()
    endtime=time.time()
    speeds[wsize]=endtime-starttime
    if STATUS: print 'took',speeds[wsize],'seconds'
    if speeds[wsize] < speeds[bestsize]:
      bestsize=wsize
    os.unlink('%s/%s' % (mountpoint,'tempfile'))
    #time.sleep(5)
    os.system('umount %s' % mountpoint)
  os.rmdir(mountpoint)
  #print speeds,bestsize,speeds[bestsize]
  return bestsize,speeds[bestsize]

def findbestrsize(nfshost,nfsmountpoint,proto='udp',testsize=65535):
  speeds={0: 9999999.0}
  bestsize=0
  bestspeed=0
  # Larger values for this give more accurate estimates but take more time to complete
  ddcount=65535  
  char='\0'
  block=''
  for i in range(0,1024):
    block=block+char
  mountpoint=tempfile.mkdtemp()
  if DEBUG: print 'Creating test file for reading'
  os.system('mount -o proto=%s %s:%s %s' % (proto,nfshost,nfsmountpoint,mountpoint))
  file=open('%s/%s' % (mountpoint,'tempfile'),'w')
  for count in range(0,testsize):
    file.write(block)
  file.close()
  os.system('umount %s' % mountpoint)
  for rsize in range(RSIZEMAX,RSIZEMIN-1,-RSIZEINC):
    if STATUS: print 'Testing',proto,'rsize of',rsize,
    os.system('mount -o rsize=%d,proto=%s %s:%s %s' % (rsize,proto,nfshost,nfsmountpoint,mountpoint))
    starttime=time.time()
    file=open('%s/%s' % (mountpoint,'tempfile'),'r')
    file.readlines()
    file.close()
    endtime=time.time()
    speeds[rsize]=endtime-starttime
    if STATUS: print 'took',speeds[rsize],'seconds'
    if speeds[rsize] < speeds[bestsize]:
      bestsize=rsize  
    os.system('umount %s' % mountpoint)
  if DEBUG: print 'Removing test file'
  os.system('mount %s:%s %s' % (nfshost,nfsmountpoint,mountpoint))
  os.unlink('%s/%s' % (mountpoint,'tempfile'))
  os.system('umount %s' % mountpoint)
  os.rmdir(mountpoint)
  return bestsize,speeds[bestsize]


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('--tcp',    dest='tcp',action="store_true",    default=False,help="Enable test using tcp connections")
    parser.add_option('--no_udp',dest='udp',action="store_false",default=True,help="Disable UDP connection testing")
    (options, args) = parser.parse_args()
    
    udpwsize=0
    udpwspeed=0
    tcpwsize=0
    tcpwspeed=0
    udprsize=0
    udpreadspeed=0
    tcprsize=0
    tcprspeed=0

    if os.geteuid() != 0:
      print 'This program requires root privileges to run'
      sys.exit(2)    
    if len(args):
      temp=args[0].split(':')
      if len(temp) != 2:
        print 'nfsserver:dictory required'
        sys.exit(1)
      else:
        server=args[0].split(':')[0]
        directory=args[0].split(':')[1]
    if len(args) == 1 and (options.tcp or options.udp):
      if options.udp:
        print 'Testing UDP mount options, this will take several minutes'
        udpwsize,udpwspeed=findbestwsize(server,directory,testsize=TESTSIZE)
        udprsize,udprspeed=findbestrsize(server,directory,testsize=TESTSIZE)
      if options.tcp:
        print 'Testing TCP mount options, this will take several minutes'
        tcpwsize,tcpwspeed=findbestwsize(server,directory,proto='tcp',testsize=TESTSIZE)
        tcprsize,tcprspeed=findbestrsize(server,directory,proto='tcp',testsize=TESTSIZE)
      print '-------------------------- Results ---------------------------------'
      if options.udp:
        print 'udpwsize',udpwsize,'udpwspeed',udpwspeed
        print 'udprsize',udprsize,'udprspeed',udprspeed
      if options.tcp:
        print 'tcpwsize',tcpwsize,'tcpwspeed',tcpwspeed
        print 'tcprsize',tcprsize,'tcprspeed',tcprspeed
      print '-------------------------- Recommendation --------------------------'
      if tcpwspeed < udpwspeed and tcprspeed < udprspeed:
        print 'Best options are:'
        print '\t -o proto=tcp,wsize=%d,rsize=%d' % (tcpwsize,tcprsize)
      else:
        print 'Best options are:'
        print '\t -o proto=udp,wsize=%d,rsize=%d' % (udpwsize,udprsize)
    else:
      print 'nfserver:directory required'
