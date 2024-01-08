"""
Read and write binary representation of python values.

The main classes are `Value` and `Container`, base classes for all other types
that have a binary representaion. They are responsible for reading and writing
binary values, keeping track of their position and size, and hashing of their
binary representation.

Specializations of the `Value` and the `Container` classes were added as they
were needed. Some examples are binary representations of python lists and
dictionaries, as well as json documents and raw files.

The `CType` uses the `struct` package to handle the actual translation between
python values and their binary representation, but it's otherwise just an
implementation detail. It uses a binary format encoded by single letters and
other abbreviations. See the `struct` module documentation for the details.
"""

import io
import os
import json
import struct
import collections
import zlib

###############################################################################

class Access:
    """
    Helper class to implement descriptors (functions called when accessing
    object members).

    The convention is to prefix the actual value of a descriptor with an
    underscore. Getter and setter functions are prefixed with `_get` and
    `_set` respectively.
    """

    def __set_name__(self, obj, name):
        self.name =     name
        self.priv = f'_{name}'
        if obj != None:
            setattr(obj, self.priv, None)

    def __get__(self, obj, objtype=None):
        getter = f'_get_{self.name}'
        if obj is None:
            return self
        elif hasattr(obj, getter):
            return getattr(obj, getter)()
        else:
            return getattr(obj, self.priv)

    def __set__(self, obj, val):
        setter = f'_set_{self.name}'
        if hasattr(obj, setter):
            getattr(obj, setter)(val)
        else:
            if getattr(obj, self.priv, None) != val:
                setattr(obj, self.priv, val)

    def __delete__(self, obj):
        raise NotImplementedError('Access cannot be deleted')

###############################################################################

class Dirty(Access):
    """
    Keep track of when a python value is not synchronized with its binary
    representation.
    """

    def __set__(self, obj, val):
        setter = f'_set_{self.name}'
        if hasattr(obj, setter):
            getattr(obj, setter)(val)
        else:
            if getattr(obj, self.priv, None) != val:
                setattr(obj, self.priv, val)
                setattr(obj, '_dirty', True)

###############################################################################

class Value:
    """
    The main class of the bufferio module.

    Provides default implementations for basic operations:
    - buffer read, write, load and save
    - tracking position and size in buffer
    - flag when value and binary are not synchronized
    - hashing
    """

    dirty    = Access()  # flag when python value and binary are not synced
    position = Dirty()   # position of binary in buffer
    size     = Dirty()   # size of binary representation
    value    = Dirty()   # the python value
    output   = Dirty()   # output file

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise RuntimeError(f'Cannot set attribute {k}')

    def __str__(self):
            return (f'dirty={self.dirty}, position={self.position},' +
                    f'size={self.size}, output file={self.output}')

    # default access handlers for descriptors

    def _set_output(self, output):
        if self._output != output:
            self._output   = output
            self._position = None
            self._dirty    = True

    def _set_position(self, position):
        if self._position != position:
            self._position = position
            self._dirty    = True

    def _set_size(self, size):
        if self._size != size:
            self._size  = size
            self._dirty = True

    def _set_value(self, value):
        if self._value != value:
            if type(self) != File:
                self._size  = None
            self._value = value
            self._dirty = True

    # default method implementations for the read, write and hash operations

    # @log_value_io
    def update(self):
        """Save python value to binary buffer"""
        if self.position is None:
            # Set position from file pointer
            self.position = self.output.tell()
            # change file pointer to end of value
            self.output.seek(self.position + self.size, io.SEEK_SET)
        if self.dirty:
            self.dirty = False

    def hash(self, hasher):
        """Calculate hash of binary representation"""
        if self.position is None or self.size is None:
            raise RuntimeError('Cannot hash without buffer location')
        self.output.seek(self.position, io.SEEK_SET)
        chunk = self.output.read(self.size)
        if len(chunk) == 0:
            raise EOFError(f'unexpected eof')
        if isinstance(hasher, list):
            hasher.append(chunk)
        else :
            hasher.update(chunk)

    raw_hash = hash

    # default method implementations for the read, write and hash operations

###############################################################################

class Container(Value):
    """
    Base class for python containers, like list and dictionary.

    Specializes the basic value operations (see `Value` class).

    Provides default implementation for basic container operations:
    - iteration
    - element access.

    Specializes operations for read, write, position, size and hashing.
    """

    def kv_iterator(self):
        """Iterator over members"""
        return enumerate(self)

    # attibute access

    def _get_dirty(self):
        return any(v.dirty for k,v in self.kv_iterator())

    def _set_dirty(self, dirty):
        for k,v in self.kv_iterator():
            v.dirty = dirty

    def _get_output(self):
        try:
            return next(self.kv_iterator())[1].output
        except StopIteration:
            return None

    def _set_output(self, output):
        for k,v in self.kv_iterator():
            if v is not None:
                v.output = output

    def _get_position(self):
        try:
            return next(self.kv_iterator())[1].position
        except StopIteration:
            return None

    def _set_position(self):
        raise RuntimeError(f'Cannot set position for {self.__class__.__name__}')

    def _get_size(self):
        return sum(v.size for k,v in self.kv_iterator())

    def _set_size(self, _):
        raise RuntimeError(f'Cannot set size for {self.__class__.__name__}')

    def _get_value(self):
        return type(self._value)((v.value for k,v in self.kv_iterator()))

    def _set_value(self, value):
        for (k,v),a in zip(self.kv_iterator(), value):
            v.value = a

    # helpers for iteration over members

    @staticmethod
    def all(method):
        def result(self, *args, **kwargs):
            for k,v in self.kv_iterator():
                getattr(v, method)(*args, **kwargs)
        return result

    @staticmethod
    def all_but(method):
        def result(self, keys, *args, **kwargs):
            for k,v in self.kv_iterator():
                if k not in keys:
                    getattr(v, method)(*args, **kwargs)
        return result

    @staticmethod
    def until(method):
        def result(self, key, *args, **kwargs):
            for k,v in self.kv_iterator():
                getattr(v, method)(*args, **kwargs)
                if k == key:
                    return
        return result

    # create specialized methods

    update          = all    .__func__('update')
    hash            = all    .__func__('hash')
    update_until    = until  .__func__('update')
    hash_until      = until  .__func__('hash')
    update_all_but  = all_but.__func__('update')
    hash_all_but    = all_but.__func__('hash')

    def read(self):
        """Safe guard for missing specializations."""
        raise RuntimeError(f'Cannot read for {self.__class__.__name__}')

    def write(self):
        """Safe guard for missing specializations."""
        raise RuntimeError(f'Cannot write for {self.__class__.__name__}')

###############################################################################

class List(Container, collections.UserList):
    """Implements python lists"""
    def __init__(self, arg = list()):
        self.data   = arg.copy()
        self._value = self.data

class BList(Container, collections.UserList):

    """Implements python lists"""
    def __init__(self, method, provider, arg = list()):
        self.data   = arg.copy()
        self._value = self.data
        self.method = method
        self.provider = (provider.compressionObj() if (not self.method and provider is not None) else provider)
        self.buff = b''
        self.BIndex = []
        self.uncompressedS = os.path.getsize(self[0]['DATA'].value)

    def _set_output(self, output):
        super()._set_output(output)

    def _set_position(self, position):
       ''' Sets position for lis, corresponding blocks respectively '''
       try:
          for blk in self:
              blk.position = position
              position += blk.size
       except StopIteration:
           return None

    def getValue(self):
        ''' Returns artefact path'''
        return self[0]['DATA'].value

    def cleanup(self):
        ''' Deletes empty blocks and resets sequencing for blocks'''
        if self.BIndex != []:
            i = 0
            for ind in self.BIndex :
                del self[ind - i]
                i += 1
            for j,blk in enumerate(self):
                blk['SEQ'].value = j
                blk['SEQ'].write()

    def process(self, kwargs, art = None):
        c_size = 0
        for block in self:
            block_Data = block['DATA']
            (chunk , self.buff) = block_Data.read((self.provider if not self.method else None), self.buff, os.path.getsize(block_Data.value))   #(self.provider if not self.method else None) added because block to be
            if (len(chunk) == 0):
                self.BIndex.append(self.index(block))
            else :
                comp_chunk = block.compress(self.method, self.provider ,chunk)
                c_size += len(comp_chunk)
                block_Data.size = len(comp_chunk)
                block.finalWrite(comp_chunk)
        self.cleanup()
        if art != None:
            art['compressedSize'] = c_size
            art['uncompressedSize'] = self.uncompressedS
        for block in self:
            block.sign(kwargs['signer']['sign'])                            # sign
            if not block.verify(kwargs['verifier']):                        # Signature verif. => not needed ?
                raise RuntimeError(f'Signature verification failed')
        return (c_size)

###############################################################################
class Dict(Container, collections.UserDict):
    """Implements python dictionaries"""

    def __init__(self, arg = dict()):
        self.data   = arg.copy()
        self._value = self.data

    def kv_iterator(self):
        return iter(self.items())

    def _get_value(self):
        return dict(map(lambda x: (x[0], x[1].value,), self.items()))

    def _set_position(self, position):
        for k,v in self.items():
            self[k].position = position
            position += self[k].size

###############################################################################

class CType(Value):
    """
    Translate between python and binary values using the struct package
    """

    fmt = Dirty()  # struct format code
    cnt = Dirty()  # struct count

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise RuntimeError(f'Cannot set value for missing key {k}')

    def _get_size(self):
        return struct.calcsize(self.fmt)

    def _set_size(self, _):
        raise AttributeError('cannot set size for ctype')

    def _get_fmt(self):
        if self._cnt is None:
            return f'!{self._fmt}'
        else:
            return f'!{self._cnt}{self._fmt}'

    def write(self):
        if self.cnt != 0:
            buf = None
            if self.cnt is None:
                buf = struct.pack(self.fmt, self.value)
            else:
                buf = struct.pack_into(self.fmt, *tuple(self.value))
            self.output.seek(self.position, io.SEEK_SET)
            self.output.write(buf)

###############################################################################

class ByteArray(Value):
    """Implements a binary array"""

    def _get_size(self):
        return None if self.value is None else len(self.value)

    def _set_size(self, size):
        if self.size != size:
            self.value = bytearray(size)

    def write(self):
        self.output.seek(self.position, io.SEEK_SET)
        self.output.write(self.value)
        
###############################################################################

class File(Value):
    """Implements a file"""

    offset = Dirty()

    def _get_size(self):
        if self._size is not None:
            return self._size
        else:
            return os.path.getsize(self.value)
    
    def write(self, chunk):
        self.output.seek(self.position, io.SEEK_SET)
        self.output.write(chunk)

    def read(self, provider = None, buff = None, size = None):
        with open(self.value, 'rb') as src:                                               #open input file for b read
            if self.offset is not None:
                src.seek(self.offset, io.SEEK_SET)                                        #block_Data.offset refers to offset in input file
                chunk = src.read(self.size)
                if len(chunk)== 0:
                    print(src, chunk, self.size, self.offset)
                    raise EOFError('unexpected EOF')
                if provider is None :
                    return (chunk, b'')
                else :                    
                    buff = buff + provider.compress(chunk)
                    if src.tell() == size:
                        rest = provider.flush()
                        buff += rest
                        return (buff, buff)
                    if len(buff) > self.size:
                        ret = buff[:self.size]
                        buff = buff[self.size:]
                        return (ret, buff)                                                  # block.size dATA                                          # flush 
                    else :
                        buff = buff
                        return (b'',buff)                                                  # nothing
            else:
                raise RuntimeError(f'Data block offset is None')
###############################################################################
