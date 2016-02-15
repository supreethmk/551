from mininet.topo import Topo

class FatTopo(Topo):
	def __init__( self,K):
		initial = 1
		Topo.__init__(self)
		ES=[] #edge
		AS=[] #aggregation
		CS=[] #core
		H=[]  #hosts

		for i in range(1,((K*K*K)/4)+1):
			H.append(self.addHost('h%s' % i))

		for i in range(1,(K*(K/2)+1)):
			ES.append(self.addSwitch('ES%s' % i,dpid=("%0.2X" % initial)))
			initial = initial+1
			for j in range(1,(K/2)+1):
				self.addLink(ES[i-1],H[((K/2)*(i-1))+j-1])
		
		for i in range(1,(K*(K/2)+1)):
			AS.append(self.addSwitch('AS%s' % i,dpid=("%0.2X" % initial)))
			initial = initial+1
				

		for i in range(1,((K/2)**2)+1):
			CS.append(self.addSwitch('CS%s' % i,dpid=("%0.2X" % initial)))
			initial = initial+1

		for i in range(1,K+1):
			for j in range(1,(K/2)+1):
				l = ((K/2)*(i-1))+j
				self.addLink(ES[l-1],AS[l-1])
				m = l-1;
				while( m >= (((K/2)*(i-1))+1)):
					self.addLink(ES[l-1],AS[m-1])
					self.addLink(ES[m-1],AS[l-1])
					m = m-1

		for i in range(1,(K/2)+1):
			for j in range(1,(K/2)+1):
				x = ((K/2)*(i-1))+j
				for l in range(1,K+1):
					self.addLink(CS[x-1],AS[(i+(K/2)*(l-1))-1])

	@classmethod
	def create(cls, K=4):
		return cls(K)

topos = {'fattopo': FatTopo.create}	
