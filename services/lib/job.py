"""
Overvåkeren

$Id: job.py,v 1.18 2003/01/03 15:49:42 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/job.py,v $
"""
import time,socket,sys,types,config,debug,mailAlert, RunQueue
from select import select
from errno import errorcode
from Socket import Socket

TIMEOUT = 5 #default, hardcoded timeout :)
DEBUG=0
class Event:
	UP = 'UP'
	DOWN = 'DOWN'

	def __init__(self,serviceid,netboxid,type,status,info,eventtype='serviceState', version=''):
		self.serviceid = serviceid
		self.netboxid = netboxid
		self.type = type
		self.status = status
		self.info = info
		self.eventtype = eventtype
		self.version = version
		self.sysname = ""
		self.handler = ""

	def setSysname(self, name):
		self.sysname=name


class JobHandler:
	def __init__(self,type,service,status=Event.UP):
		import db
		self._conf=config.serviceconf()
		self.setType(type)
		self.setServiceid(service['id'])
		self.setBoksid(service['netboxid'])
		self.setAddress(service['ip'])
		self.setArgs(service['args'])
		self.setVersion(service['version'])
		self.setSysname(service['sysname'])
		self.setStatus(status)
		self.setTimestamp(0)
		timeout = self.getArgs().get('timeout', self._conf.get("%s timeout" % self.getType(), self._conf.get('timeout',TIMEOUT)))
		self.setTimeout(int(timeout))
		self.db=db.db(config.dbconf())
		self.debug=debug.debug()
		self.alerter=mailAlert.mailAlert()
		self.debug.log("New job instance for %s:%s " % (self.getSysname(), self.getType()),6)
		self.runcount=0
		self.rq=RunQueue.RunQueue()
		
	def run(self):
		import rrd, db
		version = self.getVersion()
		status, info = self.executeTest()

		self.debug.log("%-25s %-5s -> %s" % (self.getSysname(), self.getType(),info))

		if status != self.getStatus() and self.runcount < int(self._conf.get('retry',3)):
			delay = int(self._conf.get('retry delay',5))
			self.runcount+=1
			self.debug.log(" %-25s %-5s -> State changed. Scheduling new check in %i sec..." % (self.getSysname(), self.getType(), delay))
			priority=delay+time.time()
			# Queue ourself
			self.rq.enq((priority,self))
			return

		if status != self.getStatus():
			self.debug.log("%-25s %-5s -> %s, %s" % (self.getSysname(), self.getType(), status, info),1)
			newEvent=Event(self.getServiceid(),self.getBoksid(),self.getType(),status,info)
			newEvent.setSysname(self.getSysname())
			# Post to the NAV alertq
			self.db.newEvent(newEvent)

			# Send an mail while we are waiting for the
			# NAV alertengine to function properly
			self.alerter.put(newEvent)
			self.setStatus(status)
		
		if version != self.getVersion() and self.getStatus() == Event.UP:
			self.db.newEvent(Event(self.getServiceid(),self.getBoksid(), self.getType(), status, info, eventtype="version", version=self.getVersion()))

		try:
			rrd.update(self.getServiceid(),'N',self.getStatus(),self.getResponsetime())
		except Exception,e:
			self.debug.log("rrd update failed for %s:%s [%s]" % (self.getSysname(),self.getType(),e),3)
		self.setTimestamp()
		self.runcount=0


	def executeTest(self):
		start = time.time()
		try:
			status,info = self.execute()
		except Exception,info:
			status = Event.DOWN
			info = str(info)
		self.setResponsetime(time.time()-start)
		return status, info

	def setServiceid(self,serviceid):
		self._serviceid = serviceid
	def getServiceid(self):
		return self._serviceid
	def setBoksid(self,boksid):
		self._boksid = boksid
	def getBoksid(self):
		return self._boksid
	def getResponsetime(self):
		return self._usage
	def setSysname(self, sysname):
		self._sysname=sysname
	def getSysname(self):
		if self._sysname:
			return self._sysname
		else:
			return self.getAddress()
	def setResponsetime(self,usage):
		self._usage = usage
	def getStatus(self):
		return self._status
	def setStatus(self,status):
		self._status = status
	def getTimestamp(self):
		return self._timestamp
	def setTimestamp(self,when = -1):
		if when == -1:
			when = time.time()
		self._timestamp= when
	def setTimeout(self,value):
		self._timeout = value
	def getTimeout(self):
		return self._timeout
	def setArgs(self,args):
		self._args = args
	def getArgs(self):
		return self._args
	def setType(self,type):
		self._type = type
	def getType(self):
		return self._type
	def getAddress(self):
		return self._address
	def setAddress(self,address):
		self._address = address
	def setVersion(self,version):
		self._version = version
	def getVersion(self):
		return self._version
	def __eq__(self,obj):
		return self.getServiceid() == obj.getServiceid() and self.getArgs() == obj.getArgs() and self.getAddress() == obj.getAddress()
	def __cmp__(self,obj):
		return self.getTimestamp().__cmp__(obj.getTimestamp())
	def __hash__(self):
		value = self.getServiceid() + self.getArgs().__str__().__hash__() + self.getAddress().__hash__()
		value = value % 2**31
		return int(value)
	def __repr__(self):
		s = '%i: %s %s %s' % (self.getServiceid(),self.getType(),str(self.getAddress()),str(self.getArgs()))
		return s.ljust(60) + self.getStatus()


