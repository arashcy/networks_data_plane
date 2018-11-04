import queue
import threading

## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    dst_addr_S_length = 5
    offset_length = 5
    flag_length = 5

    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, dst_addr, data_S, offset, flag):
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.offset= offset
        self.flag= flag
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        length = str(self.dst_addr).zfill(self.dst_addr_S_length)
        offset_S= str(self.offset).zfill(self.offset_length)
        flag_S= str(self.flag).zfill(self.flag_length)
        byte_S = length + offset_S + flag_S + self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_add = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        offset = int(byte_S[NetworkPacket.dst_addr_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.offset_length])
        flag = int(byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.offset_length: NetworkPacket.dst_addr_S_length + NetworkPacket.offset_length + NetworkPacket.flag_length])
        data_S = byte_S[NetworkPacket.dst_addr_S_length  + NetworkPacket.offset_length + NetworkPacket.flag_length: ]
        return self(dst_add, data_S, offset, flag)
    

    

## Implements a network host for receiving and transmitting data
class Host:

    number=0
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)

    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        counter=50
        offset=0
        i=0
        string_S=""
        message=data_S

        if(self.out_intf_L[self.number].mtu<50):
            while counter!=0:
                if counter<=30:
                    print("IM HERE2")
                    p = NetworkPacket(dst_addr, message, 0, offset)
                    self.out_intf_L[i].put(p.to_byte_S()) #send packets always enqueued successfully
                    print('%s: sending smaller datagram "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
                    offset=0
                    counter=0
                else:
                    print("IM HERE1")
                    string=message[0:30]
                    message=message[30:len(data_S)]
                    p = NetworkPacket(dst_addr, string, 1, offset)
                    self.out_intf_L[i].put(p.to_byte_S()) #send packets always enqueued successfully
                    print('%s: sending smaller datagram "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
                    counter=counter-30
                    offset=30+offset
                    i=i+1
                    self.number=i
        else:
            p = NetworkPacket(dst_addr, data_S, 0, 0)
            self.out_intf_L[0].put(p.to_byte_S()) #send packets always enqueued successfully
            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))

##        if (len(data_S)>40):
##            data1, data2= data_S[:len(data_S)//2], data_S[len(data_S)//2:]
##            p1 = NetworkPacket(dst_addr, data1)
##            self.out_intf_L[0].put(p1.to_byte_S()) #send packets always enqueued successfully
##            print('%s: sending packet1 "%s" on the out interface with mtu=%d' % (self, p1, self.out_intf_L[0].mtu))
##            p2 = NetworkPacket(dst_addr, data2)
##            self.out_intf_L[0].put(p2.to_byte_S()) #send packets always enqueued successfully
##            print('%s: sending packet2 "%s" on the out interface with mtu=%d' % (self, p2, self.out_intf_L[0].mtu))
##        else:
##            p = NetworkPacket(dst_addr, data_S)
##            self.out_intf_L[0].put(p.to_byte_S()) #send packets always enqueued successfully
##            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        reconstruction=""
        i=0
        if pkt_S is not None:
            p=NetworkPacket.from_byte_S(pkt_S)
            while p.flag==1: #Until flag equal zero (last packet)
                reconstruction=reconstruction+pkt_S
                pkt_S=self.in_intf_L[i].get() #Change to next packet
                i=i+1
                p=NetworkPacket.from_byte_S(pkt_S)
                print("RIGHT NOW WE READING PART %d", i)
            print('%s: received packet "%s" on the in interface' % (self, reconstruction))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class
class Router:

    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                    # HERE you will need to implement a lookup into the 
                    # forwarding table to find the appropriate outgoing interface
                    # for now we assume the outgoing interface is also i
                    self.out_intf_L[i].put(p.to_byte_S(), True)
                    print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                        % (self, p, i, i, self.out_intf_L[i].mtu))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 

