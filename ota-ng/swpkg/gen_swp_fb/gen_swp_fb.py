import os
import argparse
import json
import swp
from collections import defaultdict
from gensignature import SignatureGen as SEC
import de_compress
import magic


###############################################################################

fileTypes = defaultdict(lambda: 'None')                 #lambda : 0x00 => return 0x00 if regular file. => Anything other than the specified types
fileTypes['application/zip'] = 'Zip'                    #compressed ordinary ? to be dfined zip not taken into consideration in de_compress.py
fileTypes['application/zlib'] = 'Zlib'                  #compressed ordinary ? to be dfined
fileTypes['application/gzip'] = 'Gzip'                  #compressed ordinary ? to be dfined
fileTypes['application/x-tar'] = 'Tar'                  # TAR file
fileTypes['application/x-xz'] = 'Xz'                    # compressed TAR (.tar.xz)


mapMethod = defaultdict(lambda: 'Error')
mapMethod['compressChunks'] = True
mapMethod['compressWhole'] = False

def file_type(file_path):
    detector = magic.Magic(mime=True)
    return detector.from_file(file_path)

def controlAlgorithm(algo):
    if algo not in de_compress.SAlgos:
        raise NotImplementedError('Unsupported algorithm')
    return algo

def supportedCFV(CFV):
    supported = [0x0106,0x0104,0x0102]
    if CFV not in supported:
        raise ValueError("container format not supported")
    return CFV

def required(arg):
    if arg is None:
        raise ValueError("Required argument not specified")
    return arg

def range_type(astr, min=0, max=64535):
    '''Used to avoid choices(x,y) => prints all possible choices if input false'''
    value = int(astr)
    if min<= value <= max:
        return value
    else:
        raise argparse.ArgumentTypeError('value not in range %s-%s'%(min,max))
###############################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate swpkg.bin with specified output path")
    parser.add_argument("--container-format", help="Container format version (0x01xx), only 0x0106 supported")          #container format argument, must be 106
    parser.add_argument("--update-manifest-data", type=str, help="Path to SWPackage manifest data (json)")                                          #SWPackage manifest (Data (json) 
    parser.add_argument("--update-manifest-schema", type=str, help="Path to SWPackage manifest schema (fbs)")                                       #SWPackage manifest schema (fbs) files)
    parser.add_argument("--artefact", type=str, nargs=2, action='append', metavar=('value','method'), help="List of artefact files (e.g., artefact_0.tar) with their type of compressio, 'compressChunks' for chunks and 'compressWhole' for whole file")
    parser.add_argument("--compress", type=str, default="None", help="specify compression algorithm (Available : zlib)")
    parser.add_argument("--key-store", type=str, default=".", help="Path to the keystore, directory containing .der files")
    parser.add_argument("--block-size", type=range_type, metavar="[1-64535]", default=768, help="maximum data size for binary package generation")                  #max at 64536, whole block with sig, ... or only data ?
    parser.add_argument("--verification", type=str, default="off", help="Turn On/Off write verification")
    parser.add_argument("--verbose", action='store_true' , help="Verbose flag")
    parser.add_argument("--estimated-speed", type=int, help="Estimated speed of operation (In kB/s, this gives indication how fast UCMS can perform update)")
    parser.add_argument("--output", type=str, default="swpkg.bin", help="Output path for swpkg.bin")
    parser.add_argument("--flatc-path", type=str, default=".", help="Flatbuffer compiler path")
    parser.add_argument("--configfile", type=str, help="Config file")

    args = parser.parse_args()
    argparse_dict = vars(args)                  # Changes key's format from x-y to x_y 

    ################### PARSING ARGS #####################
    # Parse json config file or cmdline argument

    Artefacts = []
    if args.configfile is not None:
        with open(args.configfile, 'r') as cfFile:
            cfJson_string = cfFile.read()
        config = json.loads(cfJson_string)
        argparse_dict.update(config)
        Artefacts = argparse_dict['artefacts']
    else:
        if argparse_dict['artefact'] is not None:
            for art in argparse_dict['artefact']:
                Artefacts.append({'value':art[0], 'method':art[1]})

    BSize = range_type(argparse_dict['block_size'])
    Swp = required(argparse_dict['update_manifest_data'])
    SwpSch = required(argparse_dict['update_manifest_schema'])
    OFile = argparse_dict['output']
    KeyS = argparse_dict['key_store']
    Algo = argparse_dict['compress']
    Speed = argparse_dict['estimated_speed']*(10**3)
    flatcPath = argparse_dict['flatc_path']
    CFor = supportedCFV(int(required(argparse_dict['container_format']),16))

    #######################################################
    # Prepare artefact dictionary

    artefact_data = [{'data_kwargs': {'value': artefact_file['value']},'name' :os.path.basename(artefact_file['value']) , 'max_data_size': BSize, 'type' : fileTypes[file_type(artefact_file['value'])], 'method' : mapMethod[artefact_file['method']]} for artefact_file in Artefacts]
    swp_data = {'data_kwargs': {'value': Swp}, 'max_data_size': BSize , 'method' : mapMethod['compressWhole']}              #To unify processing for all blocks. Later, provider is none
    secpath = KeyS

    ##############################################################################
    # security + compression

    sec        = SEC()
    signer     = swp.UCM.signer_factory (sec,
                    swp.UCM.SignTypeDefinitions.RSA2048,
                    secpath,
                    keypath = 'ucm_dev_keypair.txt')
    verifier   = swp.UCM.verifier_factory  (sec,
                    swp.UCM.SignTypeDefinitions.RSA2048,
                    secpath,
                    keypath = 'ucm_dev_keypair.txt')
    hasher_map = swp.UCM.hasher_map_factory(sec)
    compressor = swp.UCM.initialize_compressor(de_compress.Compress)

    ###############################################################################
    # create software package

    swpkg = swp.UCM(hasher_map = hasher_map, compressor = compressor)
    spec = {
        'tag': {
            'CFV': CFor,
            'VTAG': 0,
            'BHT': swp.UCM.HashTypeDefinitions.SHA256.value                                     ## 0 = SHA256
        },
        'swp_data': swp_data,
        'swp_schema': SwpSch,
        'artefact': artefact_data,
        'algorithm': {'None': 0,'zlib': 1}[controlAlgorithm(Algo) ],
        'estimatedRate': Speed,
        'flatcP': flatcPath
    }
    output_dir = os.path.dirname(OFile)                                                         ## Create the output directory if it does not exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    swpkg.generate(spec, secpath, filename=OFile, signer=signer, verifier=verifier) 
