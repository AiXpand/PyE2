# -*- coding: utf-8 -*-
"""
Copyright (C) 2017-2021 Andrei Damian, andrei.damian@me.com,  All rights reserved.

This software and its associated documentation are the exclusive property of the creator.
Unauthorized use, copying, or distribution of this software, or any portion thereof,
is strictly prohibited.

Parts of this software are licensed and used in software developed by Lummetry.AI.
Any software proprietary to Knowledge Investment Group SRL is covered by Romanian and  Foreign Patents,
patents in process, and are protected by trade secret or copyright law.

Dissemination of this information or reproduction of this material is strictly forbidden unless prior
written permission from the author


@project: 
@description:
@created on: Mon Jul 17 08:46:16 2023
@created by: AID
"""
import os
import base64
import json
import binascii
import numpy as np
import datetime

from hashlib import sha256, md5
from threading import Lock


from cryptography.hazmat.primitives import serialization


class BCct:
  SIGN      = 'EE_SIGN'
  SENDER    = 'EE_SENDER'
  HASH      = 'EE_HASH'
  
  ADDR_PREFIX   = "aixp_"
  
  K_PEM_FILE = 'PEM_FILE'
  K_PASSWORD = 'PASSWORD'
  K_PEM_LOCATION = 'PEM_LOCATION'
  
  ERR_UNAVL_MSG = "Missing signature/sender data"
  ERR_UNAVL = 1

  ERR_SIGN_MSG = "Bad hash"
  ERR_UNAVL = 1000

  ERR_SIGN_MSG = "Bad signature"
  ERR_UNAVL = 1001
  
  AUTHORISED_ADDRS = 'authorized_addrs'
  
  
class _DotDict(dict):
  __getattr__ = dict.__getitem__
  __setattr__ = dict.__setitem__
  __delattr__ = dict.__delitem__
  
  
class VerifyMessage(_DotDict):
  def __init__(self):
    self.valid = False
    self.message = None
    self.sender = None
    
    
NON_DATA_FIELDS = [BCct.HASH, BCct.SIGN, BCct.SENDER]

class _NPJson(json.JSONEncoder):
  """
  Used to help jsonify numpy arrays or lists that contain numpy data types.
  """
  def default(self, obj):
      if isinstance(obj, np.integer):
          return int(obj)
      elif isinstance(obj, np.floating):
          return float(obj)
      elif isinstance(obj, np.ndarray):
          return obj.tolist()
      elif isinstance(obj, np.ndarray):
          return obj.tolist()
      elif isinstance(obj, datetime.datetime):
          return obj.strftime("%Y-%m-%d %H:%M:%S")
      else:
          return super(_NPJson, self).default(obj)

## RIPEMD160

# Message schedule indexes for the left path.
ML = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    7, 4, 13, 1, 10, 6, 15, 3, 12, 0, 9, 5, 2, 14, 11, 8,
    3, 10, 14, 4, 9, 15, 8, 1, 2, 7, 0, 6, 13, 11, 5, 12,
    1, 9, 11, 10, 0, 8, 12, 4, 13, 3, 7, 15, 14, 5, 6, 2,
    4, 0, 5, 9, 7, 12, 2, 10, 14, 1, 3, 8, 11, 6, 15, 13
]

# Message schedule indexes for the right path.
MR = [
    5, 14, 7, 0, 9, 2, 11, 4, 13, 6, 15, 8, 1, 10, 3, 12,
    6, 11, 3, 7, 0, 13, 5, 10, 14, 15, 8, 12, 4, 9, 1, 2,
    15, 5, 1, 3, 7, 14, 6, 9, 11, 8, 12, 2, 10, 0, 4, 13,
    8, 6, 4, 1, 3, 11, 15, 0, 5, 12, 2, 13, 9, 7, 10, 14,
    12, 15, 10, 4, 1, 5, 8, 7, 6, 2, 13, 14, 0, 3, 9, 11
]

# Rotation counts for the left path.
RL = [
    11, 14, 15, 12, 5, 8, 7, 9, 11, 13, 14, 15, 6, 7, 9, 8,
    7, 6, 8, 13, 11, 9, 7, 15, 7, 12, 15, 9, 11, 7, 13, 12,
    11, 13, 6, 7, 14, 9, 13, 15, 14, 8, 13, 6, 5, 12, 7, 5,
    11, 12, 14, 15, 14, 15, 9, 8, 9, 14, 5, 6, 8, 6, 5, 12,
    9, 15, 5, 11, 6, 8, 13, 12, 5, 12, 13, 14, 11, 8, 5, 6
]

# Rotation counts for the right path.
RR = [
    8, 9, 9, 11, 13, 15, 15, 5, 7, 7, 8, 11, 14, 14, 12, 6,
    9, 13, 15, 7, 12, 8, 9, 11, 7, 7, 12, 7, 6, 15, 13, 11,
    9, 7, 15, 11, 8, 6, 6, 14, 12, 13, 5, 14, 13, 13, 7, 5,
    15, 5, 8, 11, 14, 14, 6, 14, 6, 9, 12, 9, 12, 5, 15, 8,
    8, 5, 12, 9, 12, 5, 14, 6, 8, 13, 6, 5, 15, 13, 11, 11
]

# K constants for the left path.
KL = [0, 0x5a827999, 0x6ed9eba1, 0x8f1bbcdc, 0xa953fd4e]

# K constants for the right path.
KR = [0x50a28be6, 0x5c4dd124, 0x6d703ef3, 0x7a6d76e9, 0]


def fi(x, y, z, i):
    """The f1, f2, f3, f4, and f5 functions from the specification."""
    if i == 0:
        return x ^ y ^ z
    elif i == 1:
        return (x & y) | (~x & z)
    elif i == 2:
        return (x | ~y) ^ z
    elif i == 3:
        return (x & z) | (y & ~z)
    elif i == 4:
        return x ^ (y | ~z)
    else:
        assert False


def rol(x, i):
    """Rotate the bottom 32 bits of x left by i bits."""
    return ((x << i) | ((x & 0xffffffff) >> (32 - i))) & 0xffffffff


def compress(h0, h1, h2, h3, h4, block):
    """Compress state (h0, h1, h2, h3, h4) with block."""
    # Left path variables.
    al, bl, cl, dl, el = h0, h1, h2, h3, h4
    # Right path variables.
    ar, br, cr, dr, er = h0, h1, h2, h3, h4
    # Message variables.
    x = [int.from_bytes(block[4*i:4*(i+1)], 'little') for i in range(16)]

    # Iterate over the 80 rounds of the compression.
    for j in range(80):
        rnd = j >> 4
        # Perform left side of the transformation.
        al = rol(al + fi(bl, cl, dl, rnd) + x[ML[j]] + KL[rnd], RL[j]) + el
        al, bl, cl, dl, el = el, al, bl, rol(cl, 10), dl
        # Perform right side of the transformation.
        ar = rol(ar + fi(br, cr, dr, 4 - rnd) + x[MR[j]] + KR[rnd], RR[j]) + er
        ar, br, cr, dr, er = er, ar, br, rol(cr, 10), dr

    # Compose old state, left transform, and right transform into new state.
    return h1 + cl + dr, h2 + dl + er, h3 + el + ar, h4 + al + br, h0 + bl + cr


def ripemd160(data):
    """Compute the RIPEMD-160 hash of data."""
    # Initialize state.
    state = (0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0)
    # Process full 64-byte blocks in the input.
    for b in range(len(data) >> 6):
        state = compress(*state, data[64*b:64*(b+1)])
    # Construct final blocks (with padding and size).
    pad = b"\x80" + b"\x00" * ((119 - len(data)) & 63)
    fin = data[len(data) & ~63:] + pad + (8 * len(data)).to_bytes(8, 'little')
    # Process final blocks.
    for b in range(len(fin) >> 6):
        state = compress(*state, fin[64*b:64*(b+1)])
    # Produce output.
    return b"".join((h & 0xffffffff).to_bytes(4, 'little') for h in state)
  
# END ## RIPEMD160  

class SimpleLogger:
  def __init__(self):
    return
  
  def P(s, color=None):
    print(s, flush=True)
    return

class BaseBlockEngine:
  """
  This multiton is the base workhorse of the private blockchain. 
  
  """
  _lock: Lock = Lock()
  __instances = {}
  
  def __new__(cls, name, config, log):
    with cls._lock:
      if name not in cls.__instances:
        instance = super(BaseBlockEngine, cls).__new__(cls)
        instance._build(name=name, log=log, config=config)
        cls.__instances[name] = instance
      else:
        instance = cls.__instances[name]
    return instance
  
  def _build(
      self, 
      name, 
      config:dict, 
      log=None, 
    ):

    self.__name = name
    assert log is not None, "Logger object was not provided!"
      
    self.log = log
    self.__private_key = None
    self.__public_key = None    
    self.__password = config.get(BCct.K_PASSWORD)    
    self.__config = config
    
    pem_name = config.get(BCct.K_PEM_FILE, '_pk.pem')
    pem_folder = config.get(BCct.K_PEM_LOCATION, 'data')
    pem_fn = os.path.join(log.get_target_folder(pem_folder), pem_name)
    self.__pem_file = pem_fn
    
    self._init()
    return
  
  def P(self, s, color=None, boxed=False, **kwargs):
    if not boxed:
      s = "<BC:{}> ".format(self.__name) + s
    return self.log.P(
      s, 
      color='g' if (color is None or color.lower() not in ['r', 'red', 'error']) else color, 
      boxed=boxed, 
      **kwargs
    )
     

  def _init(self):
    self.P("Initializing Blockchain engine manager...", boxed=True, box_char='*')

    if True:
      self.P("Initializing private blockchain:\n{}".format(json.dumps(self.__config, indent=4)))
    if self.__pem_file is not None:
      try:
        self.P("Trying to load sk from {}".format(self.__pem_file))
        self.__private_key = self._text_to_sk(
          source=self.__pem_file,
          from_file=True,
          password=self.__password,
        )
        self.P("  Loaded sk from {}".format(self.__pem_file))
      except:
        self.P("  Failed to load sk from {}".format(self.__pem_file), color='r')

    if self.__private_key is None:
      self.P("Creating new private key")
      self.__private_key = self._create_new_sk()
      self._sk_to_text(
        private_key=self.__private_key,
        password=self.__password,
        fn=self.__pem_file,
      )
    self.__public_key = self._get_pk(private_key=self.__private_key)
    self.__address = self._pk_to_address(self.__public_key)
    self.P("Current address: {}.".format(self.address), boxed=True)
    self.P("Allowed list of senders: {}".format(self.allowed_list))
    return
  
 
  @staticmethod
  def _compute_hash(data : bytes, method='SHA256'):
    """
    Computes the hash of a `bytes` data message

    Parameters
    ----------
    data : bytes
      the input message usually obtained from a bynary jsoned dict.
      
    method : str, optional
      the hash algo. The default is 'HASH160'.


    Returns
    -------
    result : bytes, str
      bin and text hash.

    """
    result = None, None
    method = method.upper()
    assert method in ['HASH160', 'SHA256', 'MD5']
        
    if method == 'MD5':
      hash_obj = md5(data)
      result = hash_obj.digest(), hash_obj.hexdigest()
    elif method == 'SHA256':
      hash_obj = sha256(data)
      result = hash_obj.digest(), hash_obj.hexdigest()
    elif method == 'HASH160':
      hb_sha256 = sha256(data).digest()
      hb_h160 = ripemd160(hb_sha256)
      result = hb_h160, binascii.hexlify(hb_h160).decode()
    return result  
  
  
  @staticmethod
  def _binary_to_text(data : bytes, method='base64'):
    """
    Encodes a bytes message as text

    Parameters
    ----------
    data : bytes
      the binary data, usually a signature, hash, etc.
      
    method : str, optional
      the method - 'base64' or other. The default is 'base64'.


    Returns
    -------
    txt : str
      the base64 or hexlified text.

    """
    assert isinstance(data, bytes)
    if method == 'base64':
      txt = base64.urlsafe_b64encode(data).decode()
    else:
      txt = binascii.hexlify(data).decode()
    return txt
  
  
  @staticmethod
  def _text_to_binary(text : str, method='base64'):
    """
    Convert from str/text to binary

    Parameters
    ----------
    text : str
      the message.
      
    method : str, optional
      the conversion method. The default is 'base64'.


    Returns
    -------
    data : bytes
      the decoded binary message.

    """
    assert isinstance(text, str), "Cannot convert non text to binary"
    if method == 'base64':
      data = base64.urlsafe_b64decode(text)
    else:
      data = binascii.unhexlify(text)
    return data  

  
  @staticmethod
  def _get_pk(private_key):
    """
    Simple wrapper to generate pk from sk


    Returns
    -------
    public_key : pk
    
    """
    return private_key.public_key()
  
  
  def _get_allowed_file(self):
    """
    Return the file path for the autorized addresses
    """
    folder = self.log.base_folder
    path = os.path.join(folder, BCct.AUTHORISED_ADDRS)
    return path  
  
  def _load_and_maybe_create_allowed(self):
    fn = self._get_allowed_file()
    lst_allowed = []
    if os.path.isfile(fn):
      with open(fn, 'rt') as fh:
        lst_allowed = fh.readlines()
    else:
      self.P("WARNING: no `{}` file found. Creating empty one.".format(fn))
      with open(fn, 'wt') as fh:
        fh.write('\n')
    lst_allowed = [x.strip() for x in lst_allowed]
    return lst_allowed
      
  
  
  def _pk_to_address(self, public_key):
    """
    Given a pk object will return the simple text address.
    
    OBS: Should be overwritten in particular implementations using X962


    Parameters
    ----------
    public_key : pk
      the pk object.
      
    Returns
    -------
      text address      
    
    """
    data = public_key.public_bytes(
      encoding=serialization.Encoding.DER, # will encode the full pk information 
      format=serialization.PublicFormat.SubjectPublicKeyInfo, # used with DER
    )
    txt = BCct.ADDR_PREFIX + self._binary_to_text(data)
    return txt


  def _address_to_pk(self, address):
    """
    Given a address will return the pk object
    
    OBS: Should be overwritten in particular implementations using X962


    Parameters
    ----------
    address : str
      the text address (pk).


    Returns
    -------
    pk : pk
      the pk object.

    """
    simple_address = address.replace(BCct.ADDR_PREFIX, '')
    bpublic_key = self._text_to_binary(simple_address)
    # below works for DER / SubjectPublicKeyInfo
    public_key = serialization.load_der_public_key(bpublic_key)
    return public_key
  
  
  def _text_to_sk(self, source, from_file=False, password=None):
    """
    Construct a EllipticCurvePrivateKey from a text sk

    Parameters
    ----------
    source : str
      the text secret key or the file name if `from_file == True`.
      
    from_file: bool
      flag that allows source to be a file
      

    Returns
    -------
      sk

    """
    if from_file and os.path.isfile(source):
      self.P("Reading SK from '{}'".format(source), color='g')
      with open(source, 'rt') as fh:
        data = fh.read()
    else:
      data = source
    
    bdata = data.encode()
    if password:
      pass_data = password.encode()
    else:
      pass_data = None
    private_key = serialization.load_pem_private_key(bdata, pass_data)
    return private_key
  
  def _sk_to_text(self, private_key, password=None, fn=None):
    """
    Serialize a sk as text

    Parameters
    ----------
    private_key : sk
      the secret key object.
      
    password: str
      password to be used for sk serialization
      
    fn: str:
      text file where to save the pk

    Returns
    -------
      the sk as text string

    """
    if password:
      encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
    else:
      encryption_algorithm = serialization.NoEncryption()
      
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm        
    )     
    str_pem = pem.decode()
    if fn is not None:
      self.P("Writing PEM-encoded key to {}".format(fn), color='g')
      with open(fn, 'wt') as fh:
        fh.write(str_pem)
    return str_pem  
  
  
  def _dict_to_json(self, dct_data):
    str_data = json.dumps(dct_data, sort_keys=True, cls=_NPJson, separators=(',',':'))
    return str_data
  
  def _create_new_sk(self):
    """
    Simple wrapper to generated pk


    Returns
    -------
    private_key : sk
    
    """
    raise NotImplementedError()
    

  
  def _verify(self, public_key, signature : bytes, data : bytes):
    """
    Verifies a `pk` signature on a binary `data` package
    

    Parameters
    ----------
    public_key : pk type
      the pk object.
      
    signature : bytes
      the binary signature.
      
    data : bytes
      the binary message.


    Returns
    -------
    result: _DotDict 
      contains `result.ok` and `result.message`

    """
    raise NotImplementedError()

  
  
  def _sign(self, data : bytes, private_key, text=False):
    """
    Sign a binary message with Elliptic Curve
    

    Parameters
    ----------
    data : bytes
      the binary message.
      
    private_key : pk
      the private key object.
      
    text : bool, optional
      return the signature as text. The default is False.

    Returns
    -------
    signature as text or binary

    """
    raise NotImplementedError()  
    
      
  
  #############################################################################
  ####                                                                     ####
  ####                          Public functions                           ####
  ####                                                                     ####
  #############################################################################
  
  @property
  def address(self):
    """Returns the public address"""
    return self.__address
  
  @property
  def allowed_list(self):
    """Returns the allowed senders"""
    return self._load_and_maybe_create_allowed()
    
  
  def dict_digest(self, dct_data, return_str=True):
    """Generates the hash of a dict object given as parameter"""
    str_data = self._dict_to_json(dct_data)
    data_hash, hex_hash = self._compute_hash(str_data.encode())
    if return_str:
      return hex_hash
    else:
      return data_hash
  
  
  def save_sk(self, fn, password=None):
    """
    Saves the SK with or without password

    Parameters
    ----------
    fn : str
      SK file name.
    password : str, optional
      optional password. The default is None.

    Returns
    -------
    fn : str
      saved file name.

    """
    self.P("Serializing the private key...")
    _ = self._sk_to_text(
      private_key=self.__private_key,
      password=password,
      fn=fn
    )
    return fn
  
  
  def sign(self, dct_data: dict, add_data=True, use_digest=False) -> str:
    """
    Generates the signature for a dict object. Does not add the signature to the dict object


    Parameters
    ----------
    dct_data : dict
      the input message as a dict.
      
    add_data: bool, optional
      will add signature and address to the data dict (also digest if required). Default `True`
      
    use_digest: bool, optional  
      will compute data hash and sign only on hash

    Returns
    -------
      text signature

    """
    result = None
    assert isinstance(dct_data, dict), "Cannot sign on non-dict data"
    # copy only data fields
    dct_only_data = {k:dct_data[k] for k in dct_data if k not in NON_DATA_FIELDS}
    # jsonify
    str_data = self._dict_to_json(dct_only_data)
    # binarize
    bdata = bytes(str_data, 'utf-8')
    if use_digest:
      # compute hash
      bdata, hexdigest = self._compute_hash(bdata)
    # finally sign either full or just hash
    result = self._sign(data=bdata, private_key=self.__private_key, text=True)
    if add_data:
      # not populate dict
      dct_data[BCct.SIGN] = result
      dct_data[BCct.SENDER] = self.address
      if use_digest:
        dct_data[BCct.HASH] = hexdigest
    return result
    
  
  
  def verify(
      self, 
      dct_data: dict, 
      signature: str=None, 
      sender_address: str=None, 
      return_full_info=True,
      verify_allowed=False,
    ) -> bool:
    """
    Verifies the signature validity of a given text message

    Parameters
    ----------
    dct_data : dict
      dict object that needs to be verified against the signature.
        
    signature : str, optional
      the text encoded signature. Extracted from dict if missing
      
    sender_address : str, optional
      the text encoded public key. Extracted from dict if missing
      
    return_full_info: bool, optional
      if `True` will return more than `True/False` for signature verification
      
    verify_allowed: bool, optional
      if true will also check if the address is allowed by calling `check_allowed`

    Returns
    -------
    bool / VerifyMessage
      returns `True` if signature verifies else `False`. returns `VerifyMessage` if return_full_info

    """
    result = False
    dct_only_data = {k:dct_data[k] for k in dct_data if k not in NON_DATA_FIELDS}
    data_json = self._dict_to_json(dct_only_data)
    bdata_json = data_json.encode()
    verify_msg = VerifyMessage()
    received_digest = dct_data.get(BCct.HASH)
    if received_digest:
      # we need to verify hash and then verify signature on hash      
      bdata, hexdigest = self._compute_hash(bdata_json)
      if hexdigest != received_digest:
        verify_msg.message = "Corrupted digest!"
    else:
      # normal signature on data
      bdata = bdata_json
    #endif has hash or not
    
    if verify_msg.message is None:      
      if signature is None:
        signature = dct_data.get(BCct.SIGN)
      
      if sender_address is None:
        sender_address = dct_data.get(BCct.SENDER)
      
      
      try:
        assert sender_address is not None, 'Sender address is NULL'
        assert signature is not None, 'Signature is NULL'
        
        bsignature = self._text_to_binary(signature)
        pk = self._address_to_pk(sender_address)
        verify_msg = self._verify(public_key=pk, signature=bsignature, data=bdata)
      except Exception as exc:
        verify_msg.message = str(exc)
        verify_msg.valid = False
    #endif check if signature failed already from digesting

    verify_msg.sender = sender_address
    
    if verify_allowed and verify_msg.valid:
      if not self.is_allowed(sender_address):
        verify_msg.message = "Signature ok but address {} not in {}.".format(sender_address, BCct.AUTHORISED_ADDRS)
        verify_msg.valid = False
      #endif not allowed
    #endif ok but authorization required
    
    if return_full_info:
      result = verify_msg
    else:
      result = verify_msg.ok
    return result
  
  
  def is_allowed(self, sender_address):
    is_allowed = sender_address in self.allowed_list or sender_address == self.address
    return is_allowed
      
  
  
