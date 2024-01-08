#!/usr/bin/env python

'''Signature generator

Usage:

    gensignature.py <Signature and Hash generator >
    
Options:

    -k <Private key in hex format Ex –k ABC…12A>
    -f <Artefact file path >
    -b <Artefact in binary format Ex -b abc..d>
    -s <Hash algorithms Ex -s SHA256
            Supported algorithm  : CRC32
                                   SHA1
                                   SHA224
                                   SHA256
                                   SHA384
                                   SHA512>
    -v <verbose>
    -w <Generate private key and write to path>
    -r <Read private key from path>
    -a <signature algorithm 
            Supported algorithm  : SECP192R1
                                   SECP224R1
                                   SECP256K1
                                   SECP256R1
                                   SECP384R1
                                   SECP521R1
                                   BRAINPOOLP256R1
                                   BRAINPOOLP384R1
                                   BRAINPOOLP512R1
                                   SECT163K1
                                   SECT163R2
                                   SECT233K1
                                   SECT233R1
                                   SECT283K1
                                   SECT283R1
                                   SECT409K1
                                   SECT409R1
                                   SECT571K1
                                   SECT571R1
    >
'''

import os
import sys
import asn1
import hashlib
import secrets
import decimal
import binascii
from tinyec import registry
from getopt import getopt, GetoptError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import (ec, utils)
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature




###############################################################################

# setup

options = {
    'prvkey'   : False,
    'verbose'  : False,
    'savekey'  : False,
    'loadkey'  : False,
    'sha'      : 'SHA256',
    'alg'      : False
}

###############################################################################

# process command line options

def process_command_line(argv):
    try:
        opts, args = getopt(argv,"hf:b:k:s:vw:r:a::")
    except GetoptError:
        print('CLI option error')
        print(__doc__)
        sys.exit(1)

    global options
    for opt, arg in opts:
        if opt == '-h':
            print(__doc__)
            sys.exit(0)
        elif opt in ("-f"):
            f               = open(arg, "rb")
            data            = f.read()
            f.close()
            options['data'] = data
        elif opt in ("-b"):
            data            = bytes(arg, 'utf-8')
            options['data'] = data
        elif opt in ("-k"):         
            options['prvkey'] = arg
        elif opt in ("-v"):
            options['verbose'] = True
        elif opt in ("-s"):
            options['sha'] = arg
        elif opt in ("-w"):
            options['savekey'] = arg
        elif opt in ("-r"):
            options['loadkey'] = arg
        elif opt in ("-a"):
            options['alg']     = arg


class SignatureGen(object):


###############################################################################
# DER decod
    def der_decode(self, signature):
    
        # DER decode
        decoder = asn1.Decoder()
        decoder.start(signature)
        tag, value = decoder.read()
        sig = list(value.hex())                
    
        lower  = (int(sig[2],16)<<4) | (int(sig[3],16))
        lower  = (lower * 2) + 4
        upper  = (int(sig[lower + 2],16)<<4) | (int(sig[lower + 3],16)) 
        if (upper > 32) :
            del sig[lower + 5]
            del sig[lower + 4]      
        del sig[lower + 3]
        del sig[lower + 2]
        del sig[lower + 1]
        del sig[lower + 0]
        
        lower  = (int(sig[2],16)<<4) | (int(sig[3],16))
        if (lower > 32) :
            del sig[5]
            del sig[4]      
        del sig[3]
        del sig[2]
        del sig[1]
        del sig[0]
        sig_s = "".join(sig)
    
        if options['verbose']:
            print('Encoded Signature         : 0x%s' % value.hex())   
            print('Decoded Signature         :' , sig_s)
        return sig_s

###############################################################################
# Join Signature
    def joinsignature(self, signature, size):
    
        r        = str(hex(signature[0]))
        s        = str(hex(signature[1]))
        
        rpad = ""
        if ( len(r) < (size + 2)):
            for x in range((size + 2)- len(r)):
                rpad = rpad + '0'
            rpad = rpad + r
            r    = rpad
        spad = ""    
        if ( len(s) < (size + 2)):
            for x in range((size + 2)- len(s)):
                spad = spad + '0'
            spad = spad + s
            s    = spad
        
        rs       = r + s        
        rsraw    = rs.replace("0x", "")
        
        if options['verbose']:
            print('Signature raw             :' , rsraw)
            print('Signature size            :' , len(bytes.fromhex(rsraw)))
        return bytes.fromhex(rsraw)
        
###############################################################################
# Split Signature
    def splitsignature(self, signature):
    
        raw    = signature.hex()
        r      = raw[:len(raw)//2]
        s      = raw[len(raw)//2:]
        tuple  = ( int(r,16), int(s,16) )  
    
        if options['verbose']:
            print('Signature r               :' , hex(tuple[0]))
            print('Signature s               :' , hex(tuple[1]))
        return tuple
        
###############################################################################
# generate signature
    def generate_signature(self, prvkey, data, algorithm, size = 64):
        
        private_value = int(prvkey, 16) 
        curve         = eval("ec." + algorithm + "()")
        priv_key      = ec.derive_private_key(private_value, curve, default_backend())           
        hash          = ec.ECDSA(eval("hashes." + self.alg + "()"))
        encoded       = priv_key.sign(data, hash)
        signature     = utils.decode_dss_signature(encoded)        
      
        if options['verbose']:
            print('Signature Algorithm       :', algorithm)
            print('Private key               : 0x%x' % priv_key.private_numbers().private_value)
            print('Decoded Signature r       :', hex(signature[0]))
            print('Decoded Signature s       :', hex(signature[1]))            
            
        return self.joinsignature(signature, size)
    
##############################################################################
# """
#       Generates an RSA 2048 signature using a private key and a pre-calculated digest (hash).
#     Arguments:
#         priv_key {string} -- The private key to be used for signing.
#         digest {string} -- The pre-calculated digest (hash) to be signed.
#     Returns:
#         {string} -- The RSA 2048 signature generated.
# """
    
    def generate_signature_rsa(self,private_key, digest):

        chosen_hash = hashes.SHA256()

        rsa_key = serialization.load_der_private_key(
            private_key,
            password=None,
            backend=default_backend()
        )
        # Calculate the signature
        signature = rsa_key.sign(
            digest,
            padding.PKCS1v15(),
            utils.Prehashed(chosen_hash)
        )

        return signature
    
###############################################################################
# generate Hash

    def initialize_hash(self, hashtype):

        self.alg = hashtype
        if (self.alg == 'CRC32'):
            self.obj =[]
        else:
            self.obj = hashlib.new(self.alg)
        return self.obj
        
    def update_hash(self, data):
        
        if (self.alg == 'CRC32'):
            self.obj.append(data)
        else:
            self.obj.update(data)
        
    def generate_hash(self):

        size = 8
        if (self.alg == 'CRC32'):
            data = b''.join(self.obj)
            hash = (hex(binascii.crc32(data)))
        else:
            hash = self.obj.hexdigest()
            size = self.obj.digest_size
    
        if options['verbose']:
            print('Hash Type                 :' , self.alg)
            print('Hash value                :' , hash)
            print('Hash size                 :' , size)            
        
        return hash
        
###############################################################################
# generate Private key

    def genprivatekey(self, algorithm):

        curve   = registry.get_curve(algorithm)

        privKey = secrets.randbelow(curve.field.n)
        pubKey  = privKey * curve.g
        if options['verbose']:
            print('Generated Private key     :' , hex(privKey))
        return hex(privKey)
        
###############################################################################
# generate Public key

    def genpublickey(self, privKey, algorithm):

        curve     = eval("ec." + algorithm + "()")
        priv_key  = ec.derive_private_key(int(privKey, 16) , curve, default_backend())
        pub_key   = priv_key.public_key() 
        publickey = pub_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint).hex()
        
        if options['verbose']:
            print('Generated Public key      :' , publickey)
            
        return publickey
        
###############################################################################
# Store key

    def storekey(self, privKey, publickey, path):

        data = "Private key :" + str(prvkey) + "\n"
        data = data + "Public key  :0x" + str(publickey)
        f = open(path, "w")
        f.write(data)
        f.close()
        if options['verbose']:
            print('Keypair saved at          :' , path)      
        
        
###############################################################################
# Load key

    def loadkey(self, path):

        f         = open(path, "r")
        data      = f.read()            
        f.close()
        b1        = data.split("\n")
        b2        = b1[0].split(":")
        if options['verbose']:
            print('Load Private from         :' , path)
            print('Saved Private key         :' , b2[1])
        return b2[1]  

###############################################################################
# Verification signature
    def verification(self, privKey, data, algorithm, signature):
        try:
            private_value = int(privKey, 16) 
            curve         = eval("ec." + algorithm + "()")
            priv_key      = ec.derive_private_key(private_value, curve, default_backend())
            public_key    = priv_key.public_key()       
            hash          = ec.ECDSA(eval("hashes." + self.alg + "()"))
            formated      = self.splitsignature(signature)
            sign          = utils.encode_dss_signature(formated[0], formated[1])
            public_key.verify(sign, data, hash)
        
            if options['verbose']:
                print('verification Success')
            
            return True
        except Exception as e:
            print(f'Error: {e}')
            return False
        

###############################################################################
# """
#       Verifies an RSA 2048 signature using a public key and a pre-calculated digest
#     Arguments:
#         pubkey  -- The public key to be used for veification.
#         digest  -- The pre-calculated digest (hash) to be signed.
#         sig     -- The signature to be verified
# """

    def verify_signature_rsa(self, pubkey, digest, sig):
        try:
            public_key = serialization.load_der_public_key(pubkey, backend=default_backend())
            chosen_hash = hashes.SHA256()
            public_key.verify(
            sig,   
            digest,
            padding.PKCS1v15(),
            utils.Prehashed(chosen_hash)
            )
            return True
        except Exception as e:
            print(f'Error: {e}')
            return False
#################################################################################

if __name__ == "__main__":
    try:        
        process_command_line(sys.argv[1:])
        obj         = SignatureGen()
        
        if options['savekey']:
            prvkey      = obj.genprivatekey(options['alg']) 
            pubkey      = obj.genpublickey (prvkey, options['alg'])
            obj.storekey(prvkey, pubkey, options['savekey'])
            options['prvkey'] = prvkey
        
        if options['loadkey']:
            options['prvkey'] = obj.loadkey(options['loadkey'])
            
        hashobj     = obj.initialize_hash(options['sha'])        
        obj.update_hash(options['data'])
        obj.update_hash(options['data'])
        hash        = obj.generate_hash()
        
        if options['alg']:
            signature = obj.generate_signature(options['prvkey'], bytes(hash, 'utf-8'), options['alg'])        
            res = obj.verification(options['prvkey'], bytes(hash, 'utf-8'), options['alg'] , signature)
        
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)