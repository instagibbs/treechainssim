import simpy
import os
import sys
import random

difficulty = sys.maxint/8
numlevels = 3
txncnt = 1

#TODO
#1) Get the chain structure correct to gather statistics about mining times
#2) Add transaction fees
#3) Figure out orphaning
#4) Figure out way to simulate mining wait times other than explicitly?

'''
For representing connectedness to higher chains
I'll take the time to code up the backtracking necessary
'''

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

	def copy(self):
		chain = Chain(self.parent)
		chain.lchild = self.lchild
		chain.rchild = self.rchild
		for block in self.blocks:
			chain.blocks.append(block.copy())
		return chain

	def addChild(self, child, rightleft):
		if rightleft == 0:
			self.lchild = child
		else:
			self.rchidl = child

	def addBlock(self, block):
		self.blocks.append(block)

	def length(self):
		return len(self.blocks)

	#def difficulty(self):
		
		

#Always make new block when you add new transaction
class Block(object):
	def __init__(self):
		self.ldesc = None
		self.rdesc = None

	def __init__(self, env, transactions, level, previous):
		self.env = env
		self.age = 0 #env ages this one by one
		self.transactions = transactions
		self.ldesc = None
		self.rdesc = None
		self.prefix = transactions[0].hash[0:level-1] #We assume same prefix through block level
		self.parent = None #When hash is low enough, blocks are linked
		self.level = level
		self.orphaned = False
		self.previous = previous
		self.difficulty = 1 #Need to figure out exact method, for now block depth as proxy
		self.conf = 0
		self.conftimes = [] #Store age during confs
		self.action = env.process(self.run())

	#Need to test when this increments
	def run(self):
		while True:
			self.age += 1
			yield self.env.timeout(1)
		
	#Copy gets "refreshed" block, to re-mine
	def copy(self):
		return Block(self.env, self.transactions, self.level, self.previous)
		
	#def setLDesc(self, ldesc):
	#	self.ldesc

	#def setParent(self, parent):


class Miner(object):
	def __init__(self, env, minerid):
       		self.env = env
		self.branch = genHash(numlevels-1)
		self.id = minerid
		self.profit = 0.
		self.action = env.process(self.run())
		self.chains = None
		self.mempool = None
		self.blocks = None

        def run(self):
		self.chains = initChains(numlevels)
		self.fillMempool(numlevels)
		self.buildBlocks()
        	while True:
        		#print 'hello'
			#blocks = []
			

			#Check if any transactions have been orphaned from higher branches

			#Mine new transactions
			#self.mine(difficulty)

			try:
                		self.mine(difficulty)#, self.blocks)
				
			except simpy.Interrupt:
				#print('Was interrupted. Hope, the battery is full enough....
				return
			yield self.env.timeout(1)

	#Makes txns/tokens numlevels deep to mine
	def fillMempool(self, numlevels):
		txns = []
		for i in range(0,numlevels):
			txns.append([])
			token = Token(1)
			txn = Transaction(1, token, i)
			#Hack to keep txns along same branch
			#Uneeded when transactions are made ind of miners
			txn.hash = self.branch
			txns[i].append(txn)
		self.mempool = txns
			
	def buildBlocks(self):
		txns = self.mempool
		self.blocks = []
		for i in range(0, numlevels):
			if len(self.chains[i]) > 0:
				self.blocks.append(Block(self.env, txns[i], i, self.chains[i][-1]))
			else:
				self.blocks.append(Block(self.env, txns[i], i, None))				
	
	#This checks for orphaned blocks
	#def clearOrphaned(self):
		


	def mine(self, difficulty):#, blocks):
		hashval = random.randint(0,sys.maxint)
		successful = False
		link = False #Set to true when linking will start
		for i in range(0,numlevels):
			if self.blocks[i] == None:
				continue
			if hashval < difficulty/(2**(i)):
				print('Found block at level %d' % (i+1))
				successful = True
				#Add conf and age marker
				self.blocks[i].conf = 1
				self.blocks[i].conftimes.append(self.blocks[i].age)	
			
				#Link parent chain dep on hash, as well as ldesc/rdesc?
				if link == False:
					chainnum = getchainnum(self.blocks[i].prefix, i)
					self.chains[i][chainnum].addBlock(self.blocks[i])
					self.profit += 1./(2**(i))
				else:
					#Chainnum for this level
					chainnum = getchainnum(self.blocks[i].prefix, i)
					#Determine left/rightness to parent
					if self.blocks[i].prefix[i] == '0':
						self.blocks[i-1].ldesc = self.blocks[i]
					else:
						self.blocks[i-1].rdesc = self.blocks[i]
					self.blocks[i].parent = self.blocks[i-1]
					self.chains[i][chainnum].addBlock(self.blocks[i])
					#Only block reward for now
					self.profit += 1./(2**(i))
				link = True

		#If mined a block, make new txns/blocks
		if successful == True:
			self.fillMempool(numlevels)
			self.buildBlocks()


#Transactions have random hashes
class Transaction(object):
	def __init__(self, txnid, token, level):
		self.id = txnid
		self.token = token
		self.level = level
		self.hash = genHash(numlevels-1)
		self.conf = 0
	'''	
	def incConf(self):
		self.conf += 1
	'''	
	def copy(self):
		return Transaction(self.id, self.token, self.levl)


class Token(object):
	def __init__(self, currChain):
		self.currChain = currChain

	def sendToken(self, nextChain):
		self.currChain = nextChain
'''
class announcedBlocks(object):
	def __init__(self, env):
		self.blocks = []
		self.env = env
		self.action = env.process(self.run())

	def run(self):
'''		


#Takes binary string and level, returns chain number
def getchainnum(prefix, level):
	if level == 1:
		return 0
	return (int(prefix[0,level], 2))

#Creates blank chains of specified tree depth
def initChains(levels):
	chain = Chain(None)
	chains = [[chain]]
	for level in range(1,levels):
		chains.append([])
		#At each level, the parent is floor(index/2) with intmath
		for index in range(0,level):
			chain = Chain((chains[level-1][index/2]))
			chains[level].append(chain)
	return chains

#Generate hash for txn
def genHash(hashsize):
	return ('{0:0'+str(hashsize)+'b}').format(random.randint(0,2**(hashsize)-1))

#def getChainParent(level, chainnum):
#	return chainnum/2

#Need to compare chains.  
#Extremely simple for now, assumes no orphans longer than 1
#def chainIsLongest(chain):
	
#Longer chain always dominates, unless parent has referenced to non-existant child blocks
#Or child chain points to non-existant parent blocks

def longerChain(chain1, chain2):
	if chain2 == None:
		return chain1
	if chain1 == None:
		return chain2
	if chain1.length() > chain2.length():
		return chain1
	elif chain2.length() > chain1.length():
		return chain2
	else:
		#Default to current chain
		return chain1

#Make sure to get end of chain case right
def chainPairingValid(parent, child):
	childInd = 0
	for parentInd in range(0,parent.length()):
		if parent.blocks[parentInd].rdesc != None or parent.blocks[parentInd].ldesc != None:
			while child.blocks[childInd].parent == None and childInd < child.length():
				childInd += 1
			parentlink = child.blocks[childInd].parent
			llink = parent.blocks[parentInd].ldesc
			rlink = parent.blocks[parentInd].rdesc

			if parentlink != llink and parentlink != rlink:
				return False

	return True

			
			

#Update treechain1 to include treechain2 blocks/chains
def updateTreeChain(treechain1, treechain2):
	if treechain1 == None and treechain2 != None:
		treechain1 = initChains(len(treechain2))
	if treechain2 == None:
		return treechain1
	
	#Root chain only checks length. No validity to check.
	treechain1[0][0] = longerchain(treechain1[0][0],treechain2[0][0])
	#rootchain = None
	#if root == 1:
	#	rootchain = treechain1[0]
	#elif root == -1:
	#	rootchain = treechain2[0]
	#else:
		#Assume own chain will be mined
	#	rootchain = treechain1[0]

	for level in range(1,len(treechain1)):
		for chainnum in range(0,len(treechain1[level])):
			#Subsequent chains must be checked for validity with parent chain as well.
			if chainPairingValid(treechain1[level-1][chainnum/2], treechain1[level][chainnum]):
				if chainPairingValid(treechain2[level-1][chainnum/2], treechain2[level][chainnum]):
					#Check chain lengths
					treechain1[level][chainnum] = longerChain(treechain1[level][chainnum], treechain2[level][chainnum])
				else:
					#Keep chain
					continue
			else:
				if chainPairingValid(treechain2[level-1][chainnum/2], treechain2[level][chainnum]):
					treechain1[level][chainnum] = treechain2[level][chainnum]
				else:
					print 'Both treechains in comparison broken. Something is wrong'
					sys.exit()
	return treechain1
					
env = simpy.Environment()
#env.process(car(env)) #for interactions
#chain1 = Chain(None)
#chains = [[chain1]] #2-dim list for tree structure of chains
miner1 = Miner(env, 1)
#env.process()
env.run(until=15)
