"""
Copyright 2019-2022 Lummetry.AI (Knowledge Investment Group SRL). All Rights Reserved.


* NOTICE:  All information contained herein is, and remains
* the property of Knowledge Investment Group SRL.  
* The intellectual and technical concepts contained
* herein are proprietary to Knowledge Investment Group SRL
* and may be covered by Romanian and Foreign Patents,
* patents in process, and are protected by trade secret or copyright law.
* Dissemination of this information or reproduction of this material
* is strictly forbidden unless prior written permission is obtained
* from Knowledge Investment Group SRL.


@copyright: Lummetry.AI
@author: Lummetry.AI
@project: 
@description:
"""

import socket

class _MachineMixin(object):
  """
  Mixin for machine functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_MachineMixin, self).__init__()
    self.__total_memory = self.get_machine_memory(gb=True)  
    self.__total_disk = self.get_total_disk(gb=True)
    return
  
  @property 
  def total_memory(self):
    """
    Returns total memory in GBs
    """
    return self.__total_memory


  @property 
  def total_disk(self):
    """
    Returns total disk in GBs
    """
    return self.__total_disk
  

  @staticmethod
  def get_platform():
    import platform
    system = platform.system()
    release = platform.release()
    return system, release

  @staticmethod
  def get_cpu_usage():
    import psutil
    cpu = psutil.cpu_percent()
    return cpu

  @staticmethod
  def get_total_disk(gb=True):
    import psutil
    hdd = psutil.disk_usage('/')
    total_disk = hdd.total / ((1024**3) if gb else 1)
    return total_disk

  @staticmethod
  def get_avail_memory(gb=True):
    from psutil import virtual_memory
    avail_mem = virtual_memory().available / ((1024**3) if gb else 1)
    return avail_mem

  @staticmethod
  def get_avail_disk(gb=True):
    import psutil
    hdd = psutil.disk_usage('/')
    avail_disk = hdd.free / ((1024**3) if gb else 1)
    return avail_disk

  @staticmethod
  def get_machine_memory(gb=True):
    from psutil import virtual_memory
    total_mem = virtual_memory().total / ((1024**3) if gb else 1)
    return total_mem
    
  
  @staticmethod
  def get_localhost_ip():
    """
    Helps you obtain the localhost ip of the current machine

    Returns
    -------
    ip: string indicating the current machine local ip address

    """
    ip = None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      s.connect(('1.2.3.4', 1)) #use dummy ip address
      ip = s.getsockname()[0]
    except:
      ip = '127.0.0.1'
    finally:
      s.close()
    #end try-except-finally
    return ip