'''compress / decompress tool

Usage:

    de_compress.py -i <input file> -a <algorithm> -o <output dir>
    
Options:

    -i <Input file Ex -i test.tar >
    -a <Compression algorithm defaults to None Ex -a zlib>
    -o <Output path Ex -o testOutput/>
    -c <Flag to specify compress else decompress>

Example:
    de_compress.py -i test -a zlib -o output/ -c
    de_compress.py -i test.zlib -a zlib 
    >
'''


import zlib
import argparse
import os
import sys


class Compress:
    def __init__(self, algorithm):
        self.algorithm = algorithm
        
    def compress_data(self, i_Data):
        if self.algorithm == 'zlib':
            return zlib.compress(i_Data)
        elif self.algorithm == 'None':
            #No compression algorithm specified
            return i_Data
        else :
            raise NotImplementedError('Unsuported algorithm :' + self.algorithm)
        #elif self.agorith =='zip'
        
    def decompress_data(self, i_Data):
        if self.algorithm == 'zlib':
            return zlib.decompress(i_Data)
        elif self.algorithm == 'None':
            #No compression algorithm specified
            return i_Data
        else:
            raise NotImplementedError('Unsuported algorithm :' + self.algorithm)

    def compress_file(self, Data, Output_file_path):
        if self.algorithm == 'zlib':
            compressed_contents = zlib.compress(Data)
            with open(Output_file_path + '/compressed.zlib', 'wb') as compressed_file:
                compressed_file.write(compressed_contents)
        elif self.algorithm == 'None':
            #No compression algorithm specified
            pass
        else:
            raise NotImplementedError('Unsuported algorithm :' + self.algorithm)

    def decompress_file(self, Data, Output_file_path):
        if self.algorithm == 'zlib':
            decompressed_contents = zlib.decompress(Data)
            with open(Output_file_path + '/decompressed', 'wb') as decompressed_file:
                decompressed_file.write(decompressed_contents)
        elif self.algorithm == 'None':
            #No compression algorithm specified
            pass
        else:
            raise NotImplementedError('Unsuported algorithm : ' + self.algorithm)
        
    def compressionObj(self):
        if self.algorithm == 'zlib':
            return zlib.compressobj(method=zlib.DEFLATED)
        elif self.algorithm == 'None':
            #No compression algorithm specified
            return None
        else:
            raise NotImplementedError('Unsuported algorithm : ' + self.algorithm)
        
    def decompressionObj(self):
        if self.algorithm == 'zlib':
            return zlib.decompressobj()
        elif self.algorithm == 'None':
            #No compression algorithm specified
            return None
        else:
            raise NotImplementedError('Unsuported algorithm : ' + self.algorithm)   

#Dictionary of SAlgos
SAlgos = {
    'zlib' : '.zlib',
    'None' : ''
#    'gzip' : '.zip'     gzip not implemented but as example
}

if __name__ == "__main__":
    try:
        # Set up command-line arguments
        parser = argparse.ArgumentParser(description='tool to compress a file using zlib')
        parser.add_argument('-i','--input_file_path', help='Input path to the file to compress')                    #relative input file path
        parser.add_argument('-a','--algorithm', help='Specify compression algorithm',default='None')                #either zlib(gzip) or none ftm
        parser.add_argument('-o','--output_file_path', help='Output file path',default='')
        parser.add_argument('-c', '--compress', action='store_true')                                                # compression on/off flag

        # Parse arguments
        args = parser.parse_args()
        if_path=args.input_file_path
        of_path=args.output_file_path
        
        #instanciate object
        if args.algorithm in SAlgos:
            pop=Compress(args.algorithm)
        else :
            raise NotImplementedError('Unsuported algorithm : ' + args.algorithm)

        #check if_path and of_path exist
        if(os.path.isfile(if_path)):
            with open(if_path, 'rb') as file:
                    #test & Read file contents
                    if not file.readable():
                        raise RuntimeError('File not readable')
                    file_contents = file.read()
                    if(args.compress):
                        #compress
                        pop.compress_file(file_contents, of_path)
                    else :
                        #check extension & decompress
                        if(if_path.endswith(SAlgos[args.algorithm])):
                            pop.decompress_file(file_contents, of_path)
                        else:
                            raise RuntimeError('Input file not in ' + args.algorithm + ' format')
        else :
            raise NotADirectoryError('input file : ' + if_path + ' or output file : ' + of_path + ' does not exist')
        #return success
        sys.exit(0)
        
    except Exception as e:
        print(f'Error : {e}')
        #return failure
        sys.exit(1)
