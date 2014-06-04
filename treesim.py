import simpy
import os
import sys
import random
import time

target = sys.maxint/(2**14)
numlevels = 3
txncnt = 1

time = time.time()
print time
random.seed(1401714166.57)


#TODO
#0) Ask how long it takes a particular token to be able to be re-spent
#1) Figure out orphaning, record statistics
#2) Add transaction fees
#3) Figure out way to simulate mining wait times other than explicitly?
#4) Model latency

#turn into class field
neighbors = []

class Chain(object):
	def __init__(self, parent):
		#self.env = env
		self.parent = parent

		#Children aren't being used... no comparison either
		self.lchild = None
		self.rchild = None
		self.blocks = []

	def copy(self):
		chain = Chain(self.parent)
		chain.lchild = self.lchild
		chain.rchild = self.rchild
		for block in self.blocks:
			chain.blocks.append(block.carbonCopy())
		return chain

	def addChild(self, child, rightleft):
		if rightleft == 0:
			self.lchild = child
		else:
			self.rchild = child

	def addBlock(self, block):
		self.blocks.append(block)

	def length(self):
		return len(self.blocks)

	#def difficulty(self):
		
		
#Always make new block when you add new transactions
class Block(object):
	def __init__(self):
		#self.ldesc = None
		self.rdesc = None

	def __init__(self, env, transactions, level, previous, time):
		self.env = env
		self.age = 0 #how old the block is since it was "created"
		self.transactions = transactions
		#self.ldesc = None
		#self.rdesc = None
		self.desc = [None, None]
		self.prefix = transactions[0].hash[0:level] #We assume same prefix through block level
		self.parent = None #When hash is low enough, blocks are linked
		self.level = level
		self.orphaned = False
		self.previous = previous
		self.difficulty = 1 #Need to figure out exact method, for now block depth as proxy
		self.conf = 0
		self.conftimes = [] #Store age during confs, says how long first conf took, etc
		self.action = env.process(self.run())
		self.time = time #Env time when it gets put in block. "timestamp"

	#Need to test when this increments
	def run(self):
		while True:
			#Age breaks equality, for now. Fix later
			#self.age += 1
			yield self.env.timeout(1)
		
	#Copy gets "refreshed" block, to re-mine
	def copy(self):
		return Block(self.env, self.transactions, self.level, self.previous, self.time)

	#Need to make sure parents/links are to same place
	def carbonCopy(self):
		block = Block(self.env, self.transactions, self.level, self.previous, self.time)
		#print block.action
		block.age = self.age
		block.desc = self.desc
		block.prefix = self.prefix
		block.parent = self.parent #As long as __eq__ is correct, should be fine?
		block.difficulty = self.difficulty
		block.conf = self.conf
		block.conftimes = list(self.conftimes)
		#block.action = env.process(block.run())
				
		return block

	#Need to make sure txn comparison working as well
	def __eq__(self, other):
		if other == None:
			return False

		#Don't pop if same exact struct
		if self.__repr__() == other.__repr__():
			return True

		selfrun = self.__dict__.pop("action")
		#print other.__dict__
		otherrun = other.__dict__.pop("action")
		#print '------------------------------'
		same = self.__dict__ == other.__dict__
		self.__dict__["action"] = selfrun
		other.__dict__["action"] = otherrun 
		#print other.__dict__
		#print 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
		return same

	def __ne__(self, other):
		if other == None:
			return True
		
		return not self.__eq__(other)		

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
                		self.mine(target)#, self.blocks)
				
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
				self.blocks.append(Block(self.env, txns[i], i, self.chains[i][-1], -1))
			else:
				self.blocks.append(Block(self.env, txns[i], i, None,  -1))				

	#For now faking it, just sharing self
	def alertOnBlock(self):
		for neighbor in neighbors:
			if neighbor == self:
				continue
			neighbor.acceptBlocks(self)

	def acceptBlocks(self, neighbor):
		self.chains = updateTreeChain(self.chains, neighbor.chains)
	
	#This checks for orphaned blocks
	#def clearOrphaned(self):
		


	def mine(self, target):#, blocks):
		hashval = random.randint(0,sys.maxint)
		successful = False
		link = False #Set to true when linking will start
		for i in range(0,numlevels):
			if self.blocks[i] == None:
				continue
			if hashval < target*(2**(i)):
				if link == False:
					print '-----------------'
				chainnum = getchainnum(self.blocks[i].prefix, i)
				print 'Miner', str(self.id), 'found block at level', str(i), 'chainnum:', str(chainnum), 'time:', self.env._now

				self.blocks[i].time = self.env._now
				successful = True
				#Add conf and age marker
				self.blocks[i].conf = 1
				self.blocks[i].conftimes.append(self.blocks[i].age)	
			
				#Link parent chain dep on hash, as well as ldesc/rdesc?
				if link == False:
					
					self.chains[i][chainnum].addBlock(self.blocks[i])
					self.profit += 1./(2**(i))
				else:
					#Chainnum for this level
					chainnum = getchainnum(self.blocks[i].prefix, i)
					#Determine left/rightness to parent
					if self.blocks[i].prefix[i-1] == '0':
						self.blocks[i-1].desc[0] = self.blocks[i]
					else:
						self.blocks[i-1].desc[1] = self.blocks[i]
					self.blocks[i].parent = self.blocks[i-1]
					self.chains[i][chainnum].addBlock(self.blocks[i])
					#Only block reward for now
					self.profit += 1./(2**(i))
				link = True

		#If mined a block, make new txns/blocks
		if successful == True:
			self.alertOnBlock()
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

	def __eq__(self, other):
		return self.__dict__ == other.__dict__

	def __ne__(self, other):
		return not self.__eq__(other)

#Tokens will be memory shared
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
	if level == 0:
		return 0
	return int(prefix[0:level], 2)

#Creates blank chains of specified tree depth
def initChains(levels):
	chain = Chain(None)
	chains = [[chain]]
	for level in range(1,levels):
		chains.append([])
		#At each level, the parent is floor(index/2) with intmath
		for index in range(0, 2**level):
			chain = Chain((chains[level-1][index/2]))
			chains[level].append(chain)
			if index % 2 == 0:			
				chains[level-1][index/2].lchild = chain
			else:
				chains[level-1][index/2].rchild = chain
	return chains

#Generate hash for txn
def genHash(hashsize):
	return ('{0:0'+str(hashsize)+'b}').format(random.randint(0,2**(hashsize)-1))

def num2Hash(num, level):
	return ('{0:0'+str(level)+'b}').format(num)

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

#Does stepping along parent chain until link is expected, then looks for link on child
def chainPairingValid(parent, child, lr):
	childInd = 0
	for parentInd in range(0,parent.length()):
		if parent.blocks[parentInd].desc[lr] != None:
			#Catches null child case
			if child.length() == 0 or childInd == child.length():
				return False
			while childInd < child.length()-1 and child.blocks[childInd].parent == None:
				childInd += 1
			parentlink = child.blocks[childInd].parent
			childlink = parent.blocks[parentInd].desc[lr]
			#rlink = parent.blocks[parentInd].desc[1]

			if parentlink != parent.blocks[parentInd]:# or # and parentlink != rlink:
				return False
			if childlink != child.blocks[childInd]:
				return False

			#If continuing, need to move childInd forward one
			childInd += 1

	return True

#Return block depth in chain. -1 for failure to find	
def blockDepth(block, chain):
	depth = 0
	for i in range(0, chain.length()):
		if block == chain[-(i+1)]:
			return depth
		else:
			depth += 1
	return -1		

#Update treechain1 to include treechain2 blocks/chains
#Might not be totally correct in corner cases.
#Hopefully count orphans here?
#When replacing chains, need to update l/r pointers and whatnot
def updateTreeChain(treechain1, treechain2):

	newtreechain = initChains(numlevels)

	if treechain1 == None and treechain2 != None:
		treechain1 = initChains(len(treechain2))
	if treechain2 == None:
		return treechain1
	
	#Root chain only checks length. No validity to check.
	newtreechain[0][0] = longerChain(treechain1[0][0],treechain2[0][0]).copy()


	for level in range(1,len(treechain1)):
		for chainnum in range(0,len(treechain1[level])):
			lr = chainnum % 2
			#Subsequent chains must be checked for validity with parent chain as well.
			if chainPairingValid(newtreechain[level-1][chainnum/2], treechain1[level][chainnum], lr):
				if chainPairingValid(newtreechain[level-1][chainnum/2], treechain2[level][chainnum], lr):
					#Check chain lengths
					newtreechain[level][chainnum] = longerChain(treechain1[level][chainnum], treechain2[level][chainnum]).copy()
				else:
					#Keep chain
					continue
			else:
				if chainPairingValid(newtreechain[level-1][chainnum/2], treechain2[level][chainnum], lr):
					newtreechain[level][chainnum] = treechain2[level][chainnum].copy()
				else:
					print 'Both treechains in comparison broken. Something is wrong'
					sys.exit()
	return newtreechain

def getChainInd(block, chain):
	for i in range(0, chain.length()):
		if block == chain[i]:
			return i
	return -1

#Takes in block, travels forward and upward to highest chain linked
def findChainLinks(blockInd, level, chainnum, chains):
	
	currChain = [level, chainnum]
	currInd = blockInd

	heightTimes = []#Stores times of heights
	heightTimes.append(chains[level][chainnum].blocks[blockInd].time)

	for i in range(0,level):
		currLevel = level-i
		
		blockFound = False
		for j in range(currInd, chains[currLevel][currChainnum].length()):
		
			currBlock = chains[currLevel][currChainnum].blocks[j]

			if currBlock.parent != None:
				#currLevel -= 1
				#Take time of block that goes to next level
				heightTimes.append(currBlock.time)
				blockFound = True
				currChainnum /= 2
				currInd = getChainInd(currBlock.parent, chains[currLevel-1][currChainnum])
				break

		if not blockFound:
			#Ends function, no more links to be found
			return heightTimes
			
	return heightTimes

def analyzeChains(miner):
	print "Chain Analysis \n"
	#miner = miners[0]
	chains = miner.chains

	#Count # of blocks per chain, print out visually
	for chainlevel in chains:
		
		for chain in chainlevel:
			print str(chain.length())
			
		print "----------"
	

	#Next, compute how long it took each block to get linked to higher layers
	
					
env = simpy.Environment()
#env.process(car(env)) #for interactions
#chain1 = Chain(None)
#chains = [[chain1]] #2-dim list for tree structure of chains
miners = []
for i in range(0,4):
	miner = Miner(env, i)
	miner.branch = num2Hash(i, numlevels-1)
	neighbors.append(miner)
#miner1 = Miner(env, 1)
#miner2 = Miner(env, 2)
#neighbors.append(miner1)
#neighbors.append(miner2)
#env.process()
env.run(until=10000)
analyzeChains(neighbors[0])
