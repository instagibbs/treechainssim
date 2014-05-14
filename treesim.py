import simpy
import os
import sys
import random

difficulty = 100000
numlevels = 6

#TODO
#1) Get the chain structure correct to gather statistics about mining times
#2) Add transaction fees
#3) Figure out orphaning
#4) Figure out way to simulate mining wait times other than explicitly?

#Chain class is how we build up tree chain. 
#For now there will be just one copy, but
#can be extended for one copy for each miner
class Chain(object):
	def __init__(self, parent):
		#self.env = env
		self.parent = parent
		self.lchild = None
		self.rchild = None
		self.blocks = []

		#self.action = env.process(self.run())

#	def run(self):
#		while True:
			
#			try:
 #               		yield env.timeout(1000) #should be a better way
#			except simpy.Interrupt:
#				print('Block added')
#				self.addBlock(

	def addChild(self, child, rightleft):
		if rightleft = 0:
			self.lchild = child
		else:
			self.rchidl = child

	def addBlock(self, block):
		self.blocks.append(block)
		#Must check sub-chains for conflicts


class Block(object):
	def __init__(self):
		self.ldescendant = None
		self.rdescendant = None

	def __init__(self, transactions, level):
		self.transactions = transactions
		self.ldesc = None
		self.rdesc = None
		self.prefix = transactions[0].hash #We assume same prefix through block level
		self.parent = None
		self.level = level
		self.orphaned = False
		
	#Copy gets "refreshed" block, to re-mine
	def copy(self):
		return Block(self.transactions, self.level)
		
	#def setLDesc(self, ldesc):
	#	self.ldesc

	#def setParent(self, parent):


class Miner(object):
	def __init__(self, env, branch, minerid):
       		self.env = env
		self.branch = '{0:0'+str(numlevels)+'b}'.format(random.randint(0,64))
		self.mempool = []
		self.id = minerid
        	self.action = env.process(self.run())
		self.profit = 0.

        def run(self):
        	while True:
        		
			#Check if any transactions have been orphaned from higher branches

			#Mine new transactions
			self.mine(difficulty)

			try:
                		#yield self.env.process(self.mine(charge_duration))
			except simpy.Interrupt:
				#print('Was interrupted. Hope, the battery is full enough....

	
	#This checks for orphaned blocks
	def clearOrphaned(self):
		


	def mine(self, difficulty, blocks):
		hashval = random.randint(0,sys.maxint)
		
		
		for i in range(0,numlevels):
			if hashval < difficulty/(2**(i)):
				print('Found block at level %d' % i+1)
								
				#Link left/right chain dep on hash
				
				#Should make this function
				chainnum = int(blocks[i].prefix[0:i],2)
				
				#Chains shared for now... need to discovery dupes until changed
				chains[i][chainnum].addBlock(blocks[i])
				self.reward += 1./(2**(i))

class Transaction(object):
	def __init__(self, txnid, token, level):
		self.id = txnid
		self.token = token
		self.level = level
		self.hash = ('{0:0'+str(numlevels)+'b}').format(random.randint(0,64))
		self.conf = 0
		
	def incConf(self):
		self.conf += 1
		
	def copy(self):
		return Transaction(self.id, self.token, self.levl)


class Token(object):
	def __init__(self, currChain):
		self.currChain = currChain

	def sendToken(self, nextChain):
		self.currChain = nextChain


env = simpy.Environment()
#env.process(car(env)) #for interactions
car = Car(env)
env.process(driver(env, car))
env.run(until=15)
