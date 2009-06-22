
import time
import random
import stackless

class Sleep:
  def __init__(self):
    self.sleepingTasklets = []
    stackless.tasklet(self.ManageSleepingTasklets)()

  def Sleep(self, secondsToWait):
    channel = stackless.channel()
    endTime = time.time() + secondsToWait
    self.sleepingTasklets.append((endTime, channel))
    self.sleepingTasklets.sort()
    # Block until we get sent an awakening notification.
    channel.receive()

  def ManageSleepingTasklets(self):
    while True:
      if len(self.sleepingTasklets):
        endTime = self.sleepingTasklets[0][0]
        if endTime <= time.time():
          channel = self.sleepingTasklets[0][1]
          del self.sleepingTasklets[0]
          # We have to send something, but it doesn't matter what as it is not used.
          channel.send(None)
        elif stackless.runcount == 1:
          # We are the only tasklet running, the rest are blocked on channels sleeping.
          # We can call time.sleep until the first awakens to avoid a busy wait.
          delay = endTime - time.time()
          #print "wait delay", delay
          time.sleep(delay)
      stackless.schedule()

sleep = Sleep()

def santa(ch):
  while True:
    (kind, visitors) = ch.receive()
    print {
      "elves":"Ho, ho, ho!  Let's meet in the study!",
      "reindeer":"Ho, ho, ho!  Let's deliver toys!",
    }[kind]
    [v.send(None) for v in visitors]

def sec(ch, santa, kind, count):
  visitors = []
  while True:
    visitor = ch.receive()
    visitors.append(visitor)
    if len(visitors) == count:
      santa.send((kind, visitors))
      visitors = []
    stackless.schedule()

def worker(ch, sec, message):
  while True:
    sec.send(ch)
    ch.receive()
    print message
    stackless.schedule()
    sleep.Sleep(random.randint(0, 3))

def spawn(f, *args):
  ch = stackless.channel()
  stackless.tasklet(f)(*((ch,) + args))
  return ch

if __name__ == '__main__':
  sa = spawn(santa)
  edna = spawn(sec, sa, "elves", 3)
  robin = spawn(sec, sa, "reindeer", 9)
  [spawn(worker, edna, " Elf %d meeting in the study." % (i)) for i in xrange(1, 21)]
  [spawn(worker, robin, " Reindeer %d delivery toys." % (i)) for i in xrange(1, 10)]
  stackless.run()

