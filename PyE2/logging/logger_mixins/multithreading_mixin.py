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

import asyncio
from functools import wraps

class _MultithreadingMixin(object):
  """
  Mixin for multithreading functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_MultithreadingMixin, self).__init__()
    return

  @staticmethod
  def background(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
      loop = asyncio.get_event_loop()
      if callable(f):
        return loop.run_in_executor(None, f, *args, **kwargs)
      else:
        raise TypeError('Task must be a callable')
      #endif

    return wrapped

  @staticmethod
  def parallelise(function, data, batch=100, verbose=True):
    """
    Parameters
    ----------
    function : callback
      Function you need to run in parallel, on cpu, in order to speed up calculations. Ex: f2_score, etc
    data : List
      List containing tuples or values you need to pass to function
    batch : Integer, optional
      Data allocation of per job (Remember! A low batch increases IPC and synchronization overhead). The default is 1000.
    verbose: Boolean, optional
      Printing current status. The default is True.
    Returns
    -------
    results : List
      List of function result.
    """
    from multiprocessing import cpu_count, Pool
    from tqdm import tqdm
    if verbose:
      print('Parallelise function {} with data of length {} and batch {}'.format(function.__name__, len(data), batch))
    pool = Pool(processes=cpu_count())
    results = list(tqdm(pool.imap(function, data, batch), total=len(data), disable=not verbose))
    pool.close()
    pool.join()
    if verbose:
      print('Done parallelise function {}'.format(function.__name__))
    return results
