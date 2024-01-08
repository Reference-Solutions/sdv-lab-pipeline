import io
import os
import bufferio
import json
import sys
import binascii
from enum import Enum
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.hazmat.primitives.asymmetric import padding
import struct


#MAX_CHUNK_SIZE = 60000                              #max data block size is 64000 so max chunk size must approx 60000. >>temporary solution
TEMPOF = 'temporaryFile'
FLATC_ARGS = ' -c -b '
OMAN = "enriched_update_manifest.json"
#flatcBin = 'swp__test_swp_flatcfg_one_file.bin'

###############################################################################

# Block Type Definitions
#.tar 
class BTD(Enum):
    UCM_AUTHENTICATION_TAG                 = 0x0001#
    UCM_SOFTWARE_MANIFEST                  = 0x0003#
    UCM_SOFTWARE_PACKAGE_APPLICATION       = 0x0005
    UCM_SOFTWARE_PACKAGE_BINARY_IMAGE      = 0x0007
    BLOCK_INDEX_TABLE                      = 0x0009

class CTYPE(Enum):
    NO_COMPRESSION                         = 0x0000
    COMPRESSED_CHUNKS                      = 0x0001
    COMPRESSED_WHOLE                       = 0x0002

class CALGO(Enum):
    NONE                                   = 0x0000
    ZLIB                                   = 0x0001

class CFLAG(Enum):
    NOT_COMPRESSED                         = 0x0000
    COMPRESSED                             = 0x0001
###############################################################################

class BITR(bufferio.Dict):
# @NOTE class definition doesnt strictly follow defined anatomy

    def __init__(self):
        super().__init__({
            'OFFT':    bufferio.CType(fmt = 'Q'),
            'TSIZE':   bufferio.CType(fmt = 'Q'),
            'SIZE':    bufferio.CType(fmt = 'Q'),            # @16
            'COUNT':   bufferio.CType(fmt = 'Q'),
            'GROUP':   bufferio.CType(fmt = 'L'),
            'IDENT':   bufferio.CType(fmt = 'H'),
            'ADSIZE':  bufferio.CType(fmt = 'H'),
            'CTYPE':   bufferio.CType(fmt = 'H'),
            'CALGO':   bufferio.CType(fmt = 'H'),
            'PAD':     bufferio.CType(fmt = 'L')
            # compression
            })

    def generate(self, spec):
        self['IDENT'].value     = spec['IDENT']
        self['GROUP'].value     = spec['GROUP']
        self['CTYPE'].value     = spec['CTYPE']
        self['CALGO'].value     = spec['CALGO']
        self['TSIZE'].value     = 0
        self['COUNT'].value     = 0
        self['ADSIZE'].value    = 0
        self['PAD'   ].value    = 0
        

    def finalWrite(self):
        for obj in self.values():
            obj.write()

###############################################################################

class ATAG(bufferio.Dict):
# @NOTE class definition doesnt strictly follow defined anatomy

    def __init__(self, maps):
        self.maps = maps
        super().__init__({
            'TS':     bufferio.CType(fmt = 'Q'),
            'CFV':    bufferio.CType(fmt = 'L'),
            'ATAGS':  bufferio.CType(fmt = 'L'),            # @16
            'VTAG':   bufferio.CType(fmt = 'L'),
            'BHT':    bufferio.CType(fmt = 'H'),
            'BSS':    bufferio.CType(fmt = 'H'), # spec uses legacy 'BST'
			'CRC':    bufferio.CType(fmt = 'L'),
            'PAD':    bufferio.CType(fmt = 'L'),
            'SDP':    bufferio.CType(fmt = 'Q'),
            'SDB':    bufferio.ByteArray()
            })

    def generate(self, spec):
        self['CFV'   ].value = spec['tag']['CFV'   ]
        self['VTAG'  ].value = spec['tag']['VTAG'  ]
        self['BHT'   ].value = spec['tag']['BHT'   ]
        self['BSS'   ].value = spec['tag']['BSS'   ]
        self['CRC'   ].value = 0
        self['PAD'   ].value = 0
        self['SDP'   ].value = 0

    def update(self):
        self['SDB'  ].size  = self['BSS'].value + self['BSS'].value + 949 #Auth. sign. size + Certificate Sign. size + Cert. size       #fixed size for Cert. size ?
        super().update()
        self['ATAGS'].value = self.size
        self['ATAGS'].update()

    def sign(self, secpath, signer):
        ############################### CRC ##################################
        if(self['CFV'].value == 0x0106 or self['CFV'].value == 0x0102):
            crc = self.maps['hasher'](1)
            self.hash(crc)
            self['CRC'].value = binascii.crc32(b''.join(crc))
            self['CRC'].write()
            self.update()
        else:
            self.output.seek(self['CRC'].position, io.SEEK_SET)
            self.output.write(b'\0' * self['CRC'].size)
        ############################### SIG ##################################
        if(self['CFV'].value == 0x0106 or self['CFV'].value == 0x0104):
            hasher = self.maps['hasher'](self['BHT'].value)
            self.hash(hasher, True)
            sig = signer(hasher.digest())
            self['SDB'].value = sig
            certificate_file = "SecureAuth_End_Entity_cert.der"
            cert_path = os.path.join(secpath, certificate_file)
            with open(cert_path, 'rb') as f:
                certificate_text = f.read()
            key_file = "SecureAuth_End_Entity-priv-key.der"
            key_path = os.path.join(secpath, key_file)
            with open(key_path, "rb") as f:
                    private_key = f.read()
            chosen_hash = hashes.SHA256()
            hasher = hashes.Hash(chosen_hash, backend=default_backend())
            hasher.update(certificate_text)
            digest = hasher.finalize()
            rsa_key = serialization.load_der_private_key(
                private_key,
                password=None,
                backend=default_backend()
            )
            # Calculate the signature
            certificate_sign = rsa_key.sign(
                digest,
                padding.PKCS1v15(),
                utils.Prehashed(chosen_hash)
            )
            self['SDB'].value += certificate_text + certificate_sign
            self['SDB'].size = len(self['SDB'].value)
            self.update()
        else:
            self.output.seek(self['SDB'].position, io.SEEK_SET)
            self.output.write(b'\0' * self['SDB'].size)
        ######################################################################

    def hash(self, hasher, SIG = False):
        if SIG:
            self.hash_all_but(['SDB'], hasher)
        else :
            self.hash_all_but(['SDB','CRC'], hasher)

    def verify(self, verifier):
        if(self['CFV'].value == 0x0106 or self['CFV'].value == 0x0104):
            hasher = self.maps['hasher'](self['BHT'].value) 
            self.hash(hasher, True)
            return verifier(self['SDB'].value[:self['BSS'].value], hasher.digest())
        else:
            return True

    def finalWrite(self):
        for obj in self.values():
            obj.write()


###############################################################################

class BLOCK(bufferio.Dict):
# @NOTE class definition doesnt strictly follow defined anatomy

    def __init__(self, tag, maps, bit = None):
        self.tag  = tag
        self.maps = maps
        self.bit  = bit
        super().__init__({
            'SIZE':    bufferio.CType(fmt = 'Q'),   #@64
            'GROUP':   bufferio.CType(fmt = 'L'),   #@32
            'SEQ':     bufferio.CType(fmt = 'L'),
            'CRC':     bufferio.CType(fmt = 'L'),
            'CFLAG':   bufferio.CType(fmt = 'H'),
            'PAD':     bufferio.CType(fmt = 'H'),   # 
            'SIG':     bufferio.ByteArray(),
            'DATA':    None                         # data_type_map[IDENT]
            })

    def __updateBlockMetadata(self, bds_, rem, off, seq):               #Private method to update block's metadata
            bds  = bds_ if rem > bds_ else rem
            self['DATA'].size    = bds
            self['DATA'].offset  = off
            self['SEQ'].value    = seq
            seq                += 1
            off                += bds
            rem                -= bds
            return (bds_, rem, off, seq)

    @staticmethod
    def generator(tag, maps, bit, spec, rem = None):
        blk = BLOCK(tag ,maps, bit)
        blk.generate(spec)
        bds_ = spec['data']['args'].get('max_data_size')
        if bds_ is None:
            yield blk
            return
        Data = type(blk['DATA'])
        if type(blk['DATA']) != bufferio.File:
            raise NotImplemented(f'split BLOCK.DATA {Data.__name__}')
        if bds_ < 1:
            raise RuntimeError('max_data_size < 1')
        
        # if MAX_CHUNK_SIZE < bds_:
        #     bds_ = MAX_CHUNK_SIZE
        #     #print(" Input max size exceeds limit. Changed to ", MAX_CHUNK_SIZE)
        #     raise Warning("Input max size exceeds limit.")
        off  = 0
        seq  = 0
        if rem is None:
            rem  = blk['DATA'].size
        (bds_, rem, off, seq) = blk.__updateBlockMetadata(bds_, rem, off, seq)
        yield blk        
        while rem > 0:
            blk = BLOCK(tag, maps, bit)
            blk.generate(spec)
            (bds_, rem, off, seq) = blk.__updateBlockMetadata(bds_, rem, off, seq)
            yield blk
    
    

    def generate(self, spec):
        ''' Generate BLOCK based on given spec '''
        tag                     = self.tag
        Data                    = spec['data']['Type']
        kwargs                  = spec['data']['args']['data_kwargs']
        self['GROUP'].value     = spec['GROUP']
        self['SEQ'  ].value     = 0
        self['CRC' ].value      = 0
        self['CFLAG' ].value    = 0
        self['PAD' ].value      = 0
        self['SIG' ].size       = tag ['BSS'  ].value
        self['DATA']            = Data(**kwargs)                    # puts already defined 'value' to corresponding key 'value' in Data type. e.g. self['DATA] = bufferio.file(**{'value' : 'test.tar'})

    def sign(self, signer):
        ''' Sign BLOCK and write signature to output file in corresponding position '''
        ##########   CRC   ##########
        if(self.tag['CFV'].value == 0x0106 or self.tag['CFV'].value == 0x0102):
            crc = self.maps['hasher'](1)
            self.hash(crc)
            self['CRC'].value = binascii.crc32(b''.join(crc))
            self['CRC'].write()
        else:
            self.output.seek(self['CRC'].position, io.SEEK_SET)
            self.output.write(b'\0' * self['CRC'].size)
        ########## SIGNING ##########
        if(self.tag['CFV'].value == 0x0106 or self.tag['CFV'].value == 0x0104):
            hasher = self.maps['hasher'](self.tag['BHT'].value)
            self.hash(hasher, True)
            sig = signer(hasher.digest())
            if len(sig) != self['SIG'].size:
                raise RuntimeError('Different reserved and actual signature size')
            self['SIG'].value = sig
            self['SIG'].write()
        else:
            self.output.seek(self['SIG'].position, io.SEEK_SET)
            self.output.write(b'\0' * self['SIG'].size)

    def update(self):
        ''' Sync all python values with binary values '''
        super().update()
        self['SIZE'].value = self.size
        self['SIZE' ].update()

    def hash(self, hasher, SIG = False):
        if SIG:
            self.hash_all_but(['SIG'], hasher)
        else :
            self.hash_all_but(['SIG','CRC'], hasher)

    def verify(self, verifier):
        ''' Verify signature of BLOCK'''
        if(self.tag['CFV'].value == 0x0106 or self.tag['CFV'].value == 0x0104):
            hasher = self.maps['hasher'](self.tag['BHT'].value)
            self.hash(hasher, True)
            return verifier(self['SIG'].value, hasher.digest())
        else :
            return True

    def headSize(self):
        return self.size - self['DATA'].size

    def compress(self, method, compressor, chunk):
        ''' Compress data chunk if method is 'ch' and test if compression is beneficial '''
        if method:
            C_chunk = compressor.compress_data(chunk)
            if len(chunk) > len(C_chunk):
                self['CFLAG'].value = CFLAG.COMPRESSED.value
                return C_chunk
        self['CFLAG'].value = CFLAG.NOT_COMPRESSED.value
        return chunk

    def finalWrite(self, chunk = None):
        self.update()
        ''' Write to output file without SIG and DATA '''
        for obj in self.values():
            if obj != self['SIG'] and obj != self['DATA']:
                obj.write()
        if chunk is not None:
            self['DATA'].write(chunk)

 ###############################################################################

class BIT(BLOCK):
# @NOTE class definition doesnt strictly follow defined anatomy

    def generate(self, spec):
        ''' Generate BIT based on given spec '''
        tag = self.tag
        self['GROUP'].value     = 0
        self['SEQ'  ].value     = 0
        self['CRC' ].value      = 0
        self['CFLAG' ].value    = 0
        self['PAD' ].value      = 0
        self['SIG'].size        = tag['BSS'].value
        self['DATA']            = bufferio.List()
        for blk in spec['blocks']:
            bitr = BITR()
            bitr.generate(blk)
            self['DATA'].append(bitr) ##Data section in the 2nd block(BIT) has BITR info
    
    def finalWrite(self):
        ''' Write whole block to output file at exact position '''
        for obj in self.values():
            if obj != self['DATA']:
                obj.write()
            else:
                for item in obj:
                    item.finalWrite()   

###############################################################################

class Container(bufferio.Dict):

    def __init__(self):
        atag = ATAG(self.maps)
        super().__init__({
            'ATAG':   atag,
            'BIT':    BIT(atag, self.maps),
            'BLOCKS': bufferio.List()
            })

    def start_blocks(self):
        ''' Returns starting blocks'''
        bl = []
        for lis in self['BLOCKS']:
            for blk in lis:
                if blk['SEQ'].value == 0:
                    bl.append(blk)
        return bl

    def generate(self, spec, secpath, **kwargs):
        ''' Create actual output binary '''
                                                                                        # Instantiate and write ATAG / BIT object with given info from input
        self['ATAG'].generate(spec)                                                     ##Authentication Tag to be transmitted first
        self['BIT' ].generate(spec)                                                     ##ATAG to be followed by Block Index table
        tag = self['ATAG']
        bit = self['BIT' ]['DATA']
                                                                                        # Instantiate all needed blocks for the data inside the self['BLOCKS] dictionary
        for i,item in enumerate(spec.get('blocks', [])):
            blks = bufferio.BList(item['data']['args']['method'], self.maps['compressor'](spec['algorithm']), [*BLOCK.generator(tag, self.maps, bit, item)])
            bit [i]['COUNT'].value = len(blks)
            self['BLOCKS'].append(blks)
            
        if kwargs.get('filename') is not None:
            with open (kwargs['filename'], 'w+b') as buf:                               ## Open output file for the whole procedure
                self.output = buf                                                       ## take output buffer for the whole pkg
                self.setup()
                CUCSizes = []
                actualManifest = self['BLOCKS'][0].getValue()
                MAN_list = self.manifestUpdate(spec, buf, actualManifest)[0]
                MAN_list.update()
                estimatedSize = MAN_list.size

                ################################################## ARTEFACTS PROCESSIN #################################
                with open(actualManifest, 'r') as pFile:
                    pJson_string = pFile.read()
                swp_manifest = json.loads(pJson_string)

                for lis,art in zip(self['BLOCKS'][1:], swp_manifest['Artefact']):                                          ## Sweep all artefact blocks fill the Data key, sign + veirfy it and write in the corresponding position.
                    CUCSizes.append(lis.process( kwargs, art))
                ################################################## MANIFEST REFRESHIN ##################################
                #open Manifest and rewrite the needed infos                
                swp_manifest['SWPackage'][0]['uncompressedSoftwareClusterSize']= sum(lis.uncompressedS for lis in self['BLOCKS'][1:])
                swp_manifest['SWPackage'][0]['estimatedDurationOfOperation'] = round(swp_manifest['SWPackage'][0]['uncompressedSoftwareClusterSize'] / spec['estimatedRate'])
                swp_manifest['SWPackage'][0]['compressedSoftwarePackageSize']= sum(CUCSizes)
                pJson_string = json.dumps(swp_manifest)
                outputManifest = os.path.dirname(os.path.abspath(kwargs.get('filename'))) + '/' + OMAN
                with open(outputManifest, 'w') as pFile:
                    pFile.write(pJson_string)
                originalPos = self['BLOCKS'][0].position
                MAN_list = self.manifestUpdate(spec, buf, outputManifest, True)[0]
                MAN_list.position = originalPos
                MAN_list.process( kwargs)                                               ## MANIFEST list processing
                self.save()
                # Updating Total size value as we do not take into consideration the pading
                self['ATAG']['TS'].value -= self['BIT']['DATA'][0]['TSIZE'].value
                self['ATAG']['TS'].value += estimatedSize
                self.align()
                self['ATAG'].finalWrite()                                               # Final write for ATAG + BIT
                self['BIT'].finalWrite()
                ##################################################### ATAG + BIT ########################################
                self.sign(secpath, kwargs['signer']['sign'])                            # Signing ATAG + BIT
                if kwargs.get('verifier') is not None:                                  # Signature verif ATAG + BIT
                    if not self.verify(kwargs['verifier']):
                        raise RuntimeError('Signature verification failed')
                self['ATAG'].finalWrite()                                               # Final write for ATAG + BIT
                self['BIT'].finalWrite()
                ##################################################### VERIFICATION #######################################
                self.writeVerification()
                ##################################################### PROGR. ENDED #######################################

    def setup(self):
        ''' Initial setup, sets positions for ATAG + BIT and updates signature size values'''
        tag = self['ATAG']
        bit = self['BIT' ]['DATA']
        bss = tag ['BSS' ].value
        # set placeholder values for sizes and positions
        tag['TS'  ].value = 0
        for rec, blk in zip(bit, self.start_blocks()):
            rec['OFFT'].value = 0
            rec['SIZE'].value = 0
            rec['TSIZE'].value = 0
            blk['SIG' ].size  = bss
        super().update_all_but('BLOCKS')

    def pops(self, lis, max_dataS , fileP, fileS = None):
        ''' Replace existing list of blocks of file with new adapted list of blocks '''
        block = lis[0]
        listeIndex = self['BLOCKS'].index(lis)
        blockGroup = block['GROUP'].value
        if block['DATA'].value is not None:
            if os.path.exists(fileP):
                block['DATA'].value = fileP
            else :
                raise FileExistsError                                   # File does not exist
        speco ={
            'GROUP': blockGroup,
            'data' : {
                'Type' : bufferio.File,
                'args' : {  'data_kwargs': {'value': fileP},
                            'max_data_size': max_dataS,
                            'method' : False}                           #Manually mapping 'wh'
            }
        }
        newListe = bufferio.BList(False, None,[*BLOCK.generator(self['ATAG'], self.maps, self['BIT']['DATA'][listeIndex], speco, fileS)])
        if len(newListe) == 0:
            raise RuntimeError                                          # Generated list is empty
        self['BIT']['DATA'][listeIndex]['COUNT'].value = len(newListe)
        self['BLOCKS'].pop(listeIndex)
        self['BLOCKS'].insert(listeIndex, newListe)

    def align(self):
        start = self['BIT']['DATA'][0]['OFFT'].value + self['BIT']['DATA'][0]['TSIZE'].value
        end = self['BIT']['DATA'][1]['OFFT'].value if len(self['BIT']['DATA']) > 1 else self['ATAG']['TS'].value
        size = end - start
        self.output.seek(start, io.SEEK_SET)
        self.output.write(b'\0'* size)


    def manifestUpdate(self, spec, buf, file, actual = False):
        ''' Update old manifest list with new generated one '''
        MAN_list = self['BLOCKS'][0]
        os.system(spec['flatcP'] + FLATC_ARGS + spec['swp_schema']+ ' ' + file)
        flatcBin = os.getcwd() +'/'+ os.path.splitext(os.path.basename(file))[0]+'.bin'
        possibleSize = os.path.getsize(flatcBin) + 100
        actualSize = os.path.getsize(flatcBin)
        self.pops(MAN_list, spec['blocks'][0]['data']['args'].get('max_data_size'), flatcBin, (actualSize if actual else possibleSize))
        MAN_list = self['BLOCKS'][0]
        MAN_list.output = buf
        return (MAN_list, possibleSize)

    def save(self):
        ''' Allocates position and updates BITEntry values'''
        super().update()
        tag = self['ATAG']
        bit = self['BIT' ]['DATA']
        # update with actual positions and sizes
        tag['TS'].value = self.size
        tag['TS'].update()
        for rec, fst in zip(bit, self.start_blocks()):
            grp = rec['GROUP'].value
            rec['OFFT'].value = fst.position
            rec['COUNT'].value = len(self['BLOCKS'][grp - 1])                                               #grp - 1 : index start with 0 and groups with 1
            rec['SIZE'].value = sum(blk['DATA'].size for blk in self['BLOCKS'][grp - 1])
            rec['TSIZE'].value = rec['SIZE'].value + (rec['COUNT'].value * (fst['SIZE'].size + fst['GROUP'].size + fst['SEQ'].size + fst['CRC'].size + fst['CFLAG'].size + fst['PAD'].size + fst['SIG'].size))
            rec.update()

    def sign(self, secpath, signer):
        ''' Signing of the whole package data'''
        self['ATAG'].sign(secpath, signer)
        self['BIT' ].sign(signer)

    def verify(self, verifier):
        ''' Signature verification'''
        return (self['ATAG'].verify(verifier) and
                self['BIT' ].verify(verifier))

    def writeVerification(self):
        ''' #To be write verification. temporary usage => print python values corresponding to output file'''
        for obj in self['ATAG'].values():
            self.output.seek(obj.position)
            pep = self.output.read(obj.size)
            if obj != self['ATAG']['SDB']:
                pepP = struct.unpack(obj.fmt, pep)[0]
                if pepP != (obj.value):
                    raise RuntimeError
            else:
                if pep != (obj.value):
                    raise RuntimeError
        ATTS = ['SIZE','GROUP','SEQ','CRC','CFLAG']
        for ATTR in ATTS:
            for lis in self['BLOCKS']:
                for blk in lis:
                    self.output.seek(blk[ATTR].position)
                    pep = self.output.read(blk[ATTR].size)
                    pepP = struct.unpack(blk[ATTR].fmt, pep)[0]
                    if pepP != (blk[ATTR].value):
                        raise RuntimeError(f"AT block {self['BLOCKS'].index(lis)} for {ATTR} found is {pepP} and value is {blk[ATTR].value}")
        bit = self['BIT']['DATA']
        for i,item in enumerate(self['BLOCKS']):
            self.output.seek(bit[i]['OFFT'].position)
            pep = self.output.read(bit[i]['OFFT'].size)
            pepP = struct.unpack('>Q', pep)[0]
            if item.position != pepP:
                raise RuntimeError

###############################################################################
