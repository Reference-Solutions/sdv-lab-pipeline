import os
import json
import pkg
from enum import Enum
import warnings

###############################################################################

# UCM specific software package for development

class UCM(pkg.Container):

    ##########################################################################

    # package binary value definitions

    class HashTypeDefinitions(Enum):
        '''BHT values'''
        SHA256 = 0
        CRC32  = 1

    class SignTypeDefinitions(Enum):
        '''Signature algorithms.'''
        NONE      = 0
        SECP256R1 = 1
        RSA2048   = 2

    ##########################################################################

    # maps from manifest and package values

    @staticmethod
    def hasher_map_factory(provider):
        def hasher_map(arg):
            '''Convert from BHT to hasher object.'''
            HTD = UCM.HashTypeDefinitions
            val = {
                    HTD.SHA256.value: 'SHA256',
                    HTD.CRC32.value:  'CRC32'
                    }[arg]
            return provider.initialize_hash(val)
        return hasher_map
    
    @staticmethod
    def initialize_compressor(provider):
        def compressor(arg):
            '''Convert from arg value to compressor object'''
            val = {
                    0:      'None',
                    1:      'zlib'
                    # 2     :zip        ##Example
                    }[arg]
            return provider(val)
        return compressor

    @staticmethod
    def data_type_map(arg):
        '''Convert from BLOCK.IDENT to BLOCK.DATA type.'''
        BTD = pkg.BTD
        Json = pkg.bufferio.Json
        File = pkg.bufferio.File
        return {
                BTD.UCM_SOFTWARE_MANIFEST            .value: Json,
                BTD.UCM_SOFTWARE_PACKAGE_BINARY_IMAGE.value: File,
                BTD.UCM_SOFTWARE_PACKAGE_APPLICATION .value: File,
                }[arg]

    @staticmethod
    def artefact_type_map(arg):
        '''Convert from manifest artefact type to BTD.'''
        BTD = pkg.BTD
        return {
                'Image'         :       BTD.UCM_SOFTWARE_PACKAGE_BINARY_IMAGE.value,
                'Device'        :       BTD.UCM_SOFTWARE_PACKAGE_APPLICATION .value,
                'Application'   :       BTD.UCM_SOFTWARE_PACKAGE_APPLICATION .value,
                #Maybe additional value ?
                }[arg]
    
    @staticmethod
    def compression_type_map(arg):
        '''Convert from manifest artefact type to BTD.'''
        CTYPE = pkg.CTYPE
        return {
                True:           CTYPE.COMPRESSED_CHUNKS.value,
                False:          CTYPE.COMPRESSED_WHOLE.value,
                #Maybe additional value ?
                }[arg]
    
    @staticmethod
    def compression_algorithm_map(arg):
        '''Convert from manifest artefact type to BTD.'''
        CALGO = pkg.CALGO
        return {
                0:              CALGO.NONE.value,
                1:              CALGO.ZLIB.value,
                #Maybe additional value ?
                }[arg]

    ##########################################################################

    # security

    @staticmethod
    def signer_factory(provider, algorithm, secpath, **kwargs):
        '''Get signer object.'''
        if algorithm == UCM.SignTypeDefinitions.NONE:
            return { 'sign': lambda _: bytearray(64), 'size': 64 }
        elif algorithm == UCM.SignTypeDefinitions.SECP256R1:
            prvkey = provider.loadkey(kwargs['keypath'])
            def sign(digest):
                sig = provider.generate_signature(prvkey, digest, 'SECP256R1')
                return sig
            return { 'sign': sign, 'size': 64 }
        elif algorithm == UCM.SignTypeDefinitions.RSA2048:
            key_file = "SecureAuth_End_Entity-priv-key.der"
            key_path = os.path.join(secpath, key_file)
            with open(key_path, "rb") as f:
                private_key = f.read()
            def sign(digest):
                sig = provider.generate_signature_rsa(private_key, digest)
                return sig
            return { 'sign': sign, 'size': 256 }
        else:
            raise RuntimeError('Unknown signature algorithm')


    @staticmethod
    def verifier_factory(provider, algorithm, secpath, **kwargs):
        '''Get verifier object.'''
        if algorithm == UCM.SignTypeDefinitions.NONE:
            return lambda sig, digest: True
        elif algorithm == UCM.SignTypeDefinitions.SECP256R1:
            pubkey = provider.loadkey(kwargs['keypath'])
            def verify(sig, digest):
                return provider.verification(pubkey, digest, 'SECP256R1', sig)
            return verify
        elif algorithm == UCM.SignTypeDefinitions.RSA2048:
            pubkey_file = "SecureAuth_End_Entity-pub-key.der"
            key_path = os.path.join(secpath, pubkey_file)
            with open(key_path, "rb") as f:
                pubkey = f.read()
            def verify(sig, digest):
                return provider.verify_signature_rsa(pubkey, digest, sig)
            return verify
        else:
            raise RuntimeError('Unknown signature algorithm')


    ##########################################################################

    def __init__(self, *, hasher_map, compressor):
        self.maps = {
                'data_type': UCM.data_type_map,
                'hasher':    hasher_map,
                'compressor': compressor
                }
        super().__init__()

    def generate(self, spec_, secpath, **kwargs):
        '''Convert from manifest and artefact to IDENT and blocks.'''
        BTD  = pkg.BTD
        spec = spec_.copy()
        # get default BSS(Block Signature Size) from kwargs signer size
        if kwargs.get('signer') is not None:
            spec['tag'].setdefault('BSS', kwargs['signer']['size'])

        #####################################################################
        # Start of verification

        # check swp/swc json files and convert from manifest and artefact to BLOCK and DATA arguments
        if 'blocks' not in spec:
            blocks = []
            spec['blocks'] = blocks

            with open(spec['swp_data']['data_kwargs']['value'], 'r') as pFile:
                pJson_string = pFile.read()                          # to be adressed
            swp_manifest = json.loads(pJson_string)                 # to be adressed

            # Verify update action
            if swp_manifest['SWPackage'][0]['actionType'] == "Remove":
                sp_man=[]
                if len(spec['artefact'])>0:
                    #spec['artefact'] = []
                    warnings.warn(UserWarning)
            else:
                if isinstance(swp_manifest['Artefact'], str):
                    sp_man = json.loads(swp_manifest['Artefact'])
                else:
                    sp_man = swp_manifest['Artefact']
                # Verify number of artefact from swp_manifest
                if len(sp_man) != len(spec['artefact']):
                    raise RuntimeError(f"Number of artefact not matching, mentionned in SWP are {len(sp_man)}")
                
                # Verify names of artefact from swc_manifest + if any artefact doesnt figure in swc manifest
                for man in sp_man:
                    exists = False
                    for item in spec['artefact']:
                        if man['name'] == item['name']:
                            exists=True
                    if not exists:
                        raise RuntimeError(f"File :  {man['name']} not within artefacts")
                    
                for man in spec['artefact']:
                    exists=False
                    for item in sp_man:
                        if item['name'] == man['name']:
                            exists=True
                    if not exists:
                        raise RuntimeError(f"File : {man['data_kwargs']['value']} not specified in UPD manifest")
                    
            #####################################################################
            # Block caracteristics
            
            # Manifest block created for swp manifest
            blocks.append({  
                'IDENT': BTD.UCM_SOFTWARE_MANIFEST.value,
                'GROUP': 1,
                'SEQ':   1,
                'CTYPE': pkg.CTYPE.NO_COMPRESSION.value,
                'CALGO': pkg.CALGO.NONE.value,
                'data':  {
                    'Type': pkg.bufferio.File,                              # To be changed to new representation of json if there is one.
                    'args': spec['swp_data']
                    }
                })

            # Data blocks created for normal artefact data, with corresponding groups. groups start from 3 since 1/2 reserved for swp swc json
            for idx, (man, art) in enumerate(zip(sp_man, spec['artefact']), 2):
                if man['compressionType'] == "None":
                    if man['archiveType'] != art['type']:
                        raise TypeError(" Given artefact type in update manifest does not correspond to actual artefact type")
                else :
                    if man['compressionType'] != art['type']:
                        raise TypeError(" Given artefact type in update manifest does not correspond to actual artefact type")
                #IDENT = BTD.UCM_SOFTWARE_PACKAGE_APPLICATION.value # UCM.artefact_type_map(sp_man['artefact_type'])      # Define type kImage, kApp ...             ERR TO BE ADDRESSED
                blocks.append({
                    'IDENT': UCM.artefact_type_map(man['updateType']),
                    'GROUP': idx,
                    'SEQ':   1,
                    'CTYPE': UCM.compression_type_map(art['method']),
                    'CALGO': UCM.compression_algorithm_map(spec['algorithm']),
                    'data':  {
                        'Type': pkg.bufferio.File, #self.data_type_map(IDENT),                  # To be addressed ..            ERR TO BE ADDRESSED
                        'args': art
                        }
                    })

        super().generate(spec, secpath, **kwargs)

###############################################################################
