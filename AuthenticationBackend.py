import hashlib
import json
import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

class Nodes(object):
    def __init__(self, node_id, pub_key, address, port, reg_timestamp):
        self.node_id = node_id
        self.pub_key = pub_key
        self.address = address
        self.port = port
        self.reg_timestamp = reg_timestamp
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    @staticmethod
    def JsontoObject(line):
        obj = json.loads(line)
        node = Nodes(obj['node_id'], obj['pub_key'], obj['address'],obj['port'], obj['reg_timestamp'])
        return node

    #def validate_node(self):
    
    def AddNode(self):
        #if validated then add
        obj = open('nodes.json', 'a')
        obj.write(self.toJSON() + "\n")

    @staticmethod
    def LoadNodes():
        data = []
        with open('nodes.json') as f:
            for line in f:
                data.append(Nodes.JsontoObject(line))
        return data

class Transaction(object):
    def __init__(self, sender_id, reciever_id, tran_type, reg_timestamp):
        self.sender = sender_id #Sender can be any Organization
        self.reciever = reciever_id #Any Blockchain Node
        self.tran_type = tran_type #Save User Identity or Verify User Identity
        self.reg_timestamp = time.time()

    #validate(sender, reciever)

class UserIdentity(Transaction):
    def __init__(self, sender_id, reciever_id, tran_type, reg_timestamp, user_id, user_pub_key, hashed_Indentity):
        super().__init__(sender_id, reciever_id, tran_type, reg_timestamp)
        self.user_id = user_id
        self.user_pub_key = user_pub_key
        self.hashed_Indentity = hashed_Indentity

    #def requestNewPub()
    #when user generate new private key, the hashed identity will change for that user, because it is calculated based on user public key

class VerifyID(Transaction):
    def __init__(self, sender_id, reciever_id, tran_type, reg_timestamp, user_id, user_pub_key, hashed_Indentity):
        super().__init__(sender_id, reciever_id, tran_type, reg_timestamp)
        self.user_id = user_id
        self.user_pub_key = user_pub_key
        self.hashed_Indentity = hashed_Indentity
        #self.response = validateIdentity(self)

    def validateIdentity(self):
        #Load Transactions from blockchain
        #Start from the last one
        return True


class OrgIdentity(object):
    def __init__(self, org_id, org_name, pub_key, org_add, isBCPartner):
        self.org_id = org_id
        self.org_name = org_name
        self.pub_key = pub_key
        self.org_add = org_add
        self.isBCPartner = isBCPartner

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    @staticmethod
    def JsontoObject(line):
        obj = json.loads(line)
        org = OrgIdentity(obj['org_id'], obj['org_name'], obj['pub_key'],obj['org_add'], obj['isBCPartner'])
        return org

    
    def AddOrg(self):
        #if validated then add
        obj = open('orgs.json', 'a')
        obj.write(self.toJSON() + "\n")

    @staticmethod
    def LoadOrgs():
        data = []
        with open('orgs.json') as f:
            for line in f:
                data.append(OrgIdentity.JsontoObject(line))
        return data

class Block(object):
    def __init__(self, index, previousHash, timestamp, transactions, proof):
        self.index = index
        self.previousHash = previousHash
        self.timestamp = timestamp  
        self.transactions = transactions
        self.proof = proof
        self.currentHash = self.CalculateHash()

    def CalculateHash(self):
        value = str(self.index) + str(self.previousHash) + str(self.timestamp) + str(self.transactions) + str(self.proof)
        sha = hashlib.sha256(value.encode('utf-8'))
        return str(sha.hexdigest())

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.difficulty = 2
        self.trans = []
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
    
    def GetLatestBlock(self):
        return self.chain[-1]

    def CreateGenesisBlock(self):
        self.chain.append(Block(0,"0", time.time() , "Genesis Block Is Ready", 100))

    def GenerateNextBlock(self):
        parentBlock = self.GetLatestBlock()
        this_index = parentBlock.index + 1
        this_timestapm = time.time()
        this_transactions = self.trans
        this_previousHash = parentBlock.currentHash
        this_proof = self.ProofOfWork(parentBlock)
        new_block = Block(this_index, this_previousHash, this_timestapm, this_transactions, this_proof)
        self.trans = []
        self.chain.append(new_block)
        return new_block

    def ChainNewBlock(self, block):
        # Validate New Block
        self.chain.append(block)
    
    def ProofOfWork(self, last_block):
        current_proof = 0
        while self.ValidProof(last_block.proof, last_block.currentHash, current_proof) is False:
            current_proof += 1
        
        return current_proof

    def ValidProof(self, lastblock_proof, lastblock_hash, current_proof):
        string = (str(lastblock_proof) + str(current_proof) + str(lastblock_hash)).encode()
        guess_hash = hashlib.sha256(string).hexdigest()
        if guess_hash[:self.difficulty] == self.difficulty*"0":
            print(guess_hash)
            return True
        return False

    def IsChainValid(self, chain):
        parent_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if parent_block.currentHash != block.previousHash:
                return False

            if self.ValidProof(parent_block.proof, parent_block.currentHash, block.proof) is False:
                return False
            
            parent_block = block
            current_index += 1

        return True

    def ResolveConflicts(self):
        
        node_list = Nodes.LoadNodes()
        new_chain = None

        max_length = len(self.chain)

        for node in node_list:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                diff = response.json()['difficulty']
                chain = response.json()['chain']
                if length > max_length and self.IsChainValid(chain):
                    max_length = length
                    new_diff = diff
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True                

        return False

    def SaveToFile(self):
        if blockchain.IsChainValid(self.chain) is True:
            obj = open('chain.json', 'wb')
            obj.write(self.toJSON())

    def new_transactions(self, sender_id, reciever_id, tran_type, reg_timestamp, user_id, user_pub_key, hashed_Indentity):
        if tran_type == 'UserIdentity':
            self.trans.append(UserIdentity(sender_id, reciever_id, tran_type, reg_timestamp, user_id, user_pub_key, hashed_Indentity))
        if tran_type == 'VerifyID':
            self.trans.append(VerifyID(sender_id, reciever_id, tran_type, reg_timestamp, user_id, user_pub_key, hashed_Indentity))

        return self.GetLatestBlock().index + 1

# if blockchain.IsChainValid(blockchain.chain) is True:
#     print "Blockchain Validated+"
#     blockchain.SaveToFile()
#     print(blockchain.toJSON())
    
    
    #def validateBlock(self, block):

    #def DiscoverNewChain(self):


app = Flask(__name__)


node_identifier = str(uuid4()).replace('-','')

blockchain = Blockchain()
blockchain.CreateGenesisBlock()
print("Genesis Block Created Successfully")


@app.route('/mine', methods=['GET'])
def mine():
    block = blockchain.GenerateNextBlock()
    response = {
        'message': 'New Block Forged',
        'index': block.index,
        'transactions': block.transactions,
        'previous hash': block.previousHash, 
        'timestamp': block.timestamp, 
        'proof': block.proof,
    }
    return json.dumps(response, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain' : blockchain.chain,
        'difficulty' : blockchain.difficulty,
        'length': len(blockchain.chain)
    }
    return json.dumps(response, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        new_node = Nodes(node['node_id'], node['pub_key'], node['address'], node['port'], node['reg_timestamp'])
        new_node.AddNode()
    
    response = {
        'message': 'New Nodes have been added',
        'total_nodes': len(nodes)
    }
    return jsonify(response), 201

@app.route('/nodes/list', methods=['GET'])
def share_nodes():
    node_list = Nodes.LoadNodes()
    response = {
        'nodes': node_list
    }

    return json.dumps(response, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4), 200

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.ResolveConflicts()

    if replaced:
        response = {
            'message': 'Our Chain was replaced',
            'new_chain': blockchain.chain
        }

    else:
        response = {
            'message': 'Our Chain is authoritative',
            'new_chain': blockchain.chain
        }

    return jsonify(response), 200

@app.route('/orgs/list', methods=['GET'])
def share_orgs():
    org_list = OrgIdentity.LoadNodes()
    response = {
        'nodes': org_list
    }

    return json.dumps(response, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4), 200

@app.route('/nodes/newTrans', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender_id', 'reciever_id', 'tran_type', 'reg_timestamp', 'user_id', 'user_pub_key', 'hashed_Indentity']
    if not all(k in values for k in required):
        return 'Missing Values', 400

    index = blockchain.new_transactions(values['sender_id'], values['reciever_id'], values['tran_type'], values['reg_timestamp'], values['user_id'], values['user_pub_key'], values['hashed_Indentity'])

    response = {'message': f'Transaction will be added to block {index}'}
    return jsonify(response), 201


# @app.route('/users/register', methods=['GET'])
# @app.route('/users/verify', methods=['POST'])

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=5000)
