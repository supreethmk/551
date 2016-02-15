from ryu.base import app_manager
from ryu.controller import ofp_event, dpset
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.ip import ipv4_to_bin
import thread

vlans = {}
c = 1
K = 4	
neighbors = []
r_neighbors = []
pod_n = []
rpod_n = []
across = []


ASs=[]
for i in range(K*(K/2)+1,2*K*(K/2)+1,K/2): 
	ASs.append(i)

for i in range(1,K**3/4+1):
	for j in range(1,K**3/4+1):
		if i == j : continue
		vlans[c] = (i,j)
		c = c+1	

def ret_key(x,y):
	for key in vlans:
		if vlans[key][0] == x and vlans[key][1] == y:
			return key

def which_pod(x):
	end_h = vlans[x][1]
	for pod in range(1,K+1):
		if end_h <= pod*((K/2)**2):
			return pod


def htop(x): #for ES
	if x%((K/2)**2)%(K/2) == 0:
		return K/2 
	else:
		return (x%((K/2)**2))%(K/2)

def which_port(x):  #for AS
	if x%((K/2)**2)%(K/2)==0:
		if x%((K/2)**2) == 0:
			return K/2
		else:
			return  (x%((K/2)**2))/(K/2)
	else:
		return	((x%((K/2)**2))/(K/2))+1 

def across_out_forES(x):
	if x%(K/2)==0:
		return K
	else:
		return ((x%(K/2))%(K/2))+(K/2)			

def flow(sw,p,l,o):
		host= int(sw.id)
		ofproto = sw.ofproto
		match = sw.ofproto_parser.OFPMatch(in_port=p, dl_type=0x800, dl_vlan = l)
		action = sw.ofproto_parser.OFPActionOutput(o)
		mod = sw.ofproto_parser.OFPFlowMod(
			datapath=sw, match=match, cookie=0,
			command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
       		priority=1000,
       		flags=ofproto.OFPFF_SEND_FLOW_REM, actions=[action])
		sw.send_msg(mod)



def pod_ES(sw): 
	host = int(sw.id)
	ofproto = sw.ofproto

	for lan in pod_n:
		for port in range(1,K/2+1):
			flow(sw,port,lan,host%(K/2)+(K/2) if host%(K/2)!=0 else K)

	for lan in pod_n:
		for port in range(K/2+1,K+1):
#print lan,'vlan ',host,'sw ',vlans[lan][1],'dst ',vlans[lan][1]-((K/2)*(host-1)),'port '
#print lan,'vlan ',host,'sw ',vlans[lan][1],'dst ',htop(vlans[lan][1]),'port '
			flow(sw,port,lan,htop(vlans[lan][1]))	


def rpod_ES(sw):
	host = int(sw.id)
	ofproto = sw.ofproto

	for lan in rpod_n:
		for port in range(1,K/2+1):
			flow(sw,port,lan,host%(K/2)+(K/2) if host%(K/2)!=0 else K)

	for lan in rpod_n:
		for port in range(K/2+1,K+1):
			flow(sw,port,lan,htop(vlans[lan][1]))


def pod_AS(sw):
	host = int(sw.id)
	ofproto = sw.ofproto

	for port in range(1,K/2+1):
		for lan in pod_n:
#flow(sw,htop(vlans[lan][0]),lan,htop(vlans[lan][1]))
			flow(sw,port,lan,which_port(vlans[lan][1])) 



def rpod_AS(sw): 
	host = int(sw.id)
	ofproto = sw.ofproto

	for port in range(1,K/2+1):
		for lan in rpod_n:
#flow(sw,htop(vlans[lan][0]),lan,htop(vlans[lan][1]))
			flow(sw,port,lan,which_port(vlans[lan][1]))



def neighbors_ES(sw):
	host = int(sw.id)
	ofproto = sw.ofproto

	for lan in neighbors:
		flow(sw,vlans[lan][0]%(K/2) if vlans[lan][0]%(K/2)!=0 else K/2,lan,vlans[lan][1]%(K/2) if vlans[lan][1]%(K/2)!=0 else K/2)



def r_neighbors_ES(sw):
	host = int(sw.id)
	ofproto = sw.ofproto

	for lan in r_neighbors:
		flow(sw,vlans[lan][0]%(K/2) if vlans[lan][0]%(K/2)!=0 else K/2,lan,vlans[lan][1]%(K/2) if vlans[lan][1]%(K/2)!=0 else K/2)

def across_mod_CS(sw):
	host = int(sw.id)
	ofproto = sw.ofproto

	for port in range(1,K+1):
		for lan in across:
			flow(sw,port,lan,which_pod(lan))

def across_mod_ES(sw):
	host = int(sw.id)
	ofproto = sw.ofproto
	for lan in across:
		for port in range(1,K/2+1):
			flow(sw,port,lan,across_out_forES(host))

	for lan in across:
		for port in range(K/2+1,K+1):
			flow(sw,port,lan,htop(vlans[lan][1]))


def across_mod_AS(sw):
	host = int(sw.id)
	ofproto = sw.ofproto
	for port in range(1,K/2+1):
		for lan in across:
			flow(sw,port,lan,K/2+1)

	for port in range(K/2+1,K+1):
		for lan in across:
			flow(sw,port,lan,which_port(vlans[lan][1]))


for i in range(1,K**3/4+1,K/2):
	for j in range(i,i+(K/2)):
		for k in range(j+1,i+(K/2)):	
			if j == k : continue

			if(ret_key(j,k) not in neighbors):	
				neighbors.append(ret_key(j,k))

			if(ret_key(k,j) not in r_neighbors):	
				r_neighbors.append(ret_key(k,j))

for i in range(1,K+1):
	for j in range( (i*(K/2)**2)-((K/2)**2-1), i*(K/2)**2+1 ):
		for k in range( (i*(K/2)**2)-((K/2)**2-1), i*(K/2)**2+1 ):				
			if j == k : continue
			
			if((ret_key(j,k) not in pod_n) and (ret_key(j,k) not in neighbors) and                                                                          (ret_key(j,k) not in r_neighbors) and (ret_key(j,k) not in rpod_n)):
				#print j,',',k	
				pod_n.append(ret_key(j,k))
				#print pod_n
	
			if((ret_key(k,j) not in rpod_n) and (ret_key(k,j) not in neighbors) and                                                                         (ret_key(k,j) not in r_neighbors) and (ret_key(k,j) not in pod_n)):
				#print k,',',j	
				rpod_n.append(ret_key(k,j))
				#print rpod_n,'\n'



for i in range(1,K**3/4+1):
	for j in range(1,K**3/4+1):
		if i == j : continue
		if((ret_key(i,j) not in neighbors) and (ret_key(i,j) not in r_neighbors) and 
		   (ret_key(i,j) not in pod_n) and (ret_key(i,j) not in rpod_n)):
			if(ret_key(i,j) not in across):
				across.append(ret_key(i,j))





#print neighbors
#print r_neighbors
#print pod_n
#print rpod_n


class Controller(app_manager.RyuApp):


	def prepareESwitch(self, sw):
		host = int(sw.id)
		ofproto = sw.ofproto
		

		thread.start_new_thread(neighbors_ES,(sw,))

		thread.start_new_thread(r_neighbors_ES,(sw,))

		thread.start_new_thread(pod_ES,(sw,))

		thread.start_new_thread(rpod_ES,(sw,))

		thread.start_new_thread(across_mod_ES,(sw,))

	
	def prepareASwitch(self, sw):
		host = int(sw.id)
		ofproto = sw.ofproto

		thread.start_new_thread(pod_AS,(sw,))

		thread.start_new_thread(rpod_AS,(sw,))
	
		thread.start_new_thread(across_mod_AS,(sw,))
				
		
	def prepareCSwitch(self, sw):
		host = int(sw.id)
		ofproto = sw.ofproto
		thread.start_new_thread(across_mod_CS,(sw,))


	# the rest of the code
	@set_ev_cls(dpset.EventDP)
	def switchStatus(self, ev):
		print("Switch %s: %s!" %
			(ev.dp.id, "connected" if ev.enter else "disconnected"))
		
		if(1 <= ev.dp.id <= (K*(K/2)) ):
			self.prepareESwitch(ev.dp)

		if ev.dp.id in ASs:	
			self.prepareASwitch(ev.dp)
		
		if( 2*K*(K/2)+1 ==  ev.dp.id ):
			self.prepareCSwitch(ev.dp)
