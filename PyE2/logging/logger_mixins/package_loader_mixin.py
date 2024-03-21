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
@author: Lummetry.AI - Laurentiu
@project: 
@description:
"""

import sys

class _PackageLoaderMixin(object):
  """
  Mixin for package loader functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_PackageLoaderMixin, self).__init__()

  @staticmethod
  def package_loader(package_name, as_bool=True, return_package=False):
    """
    returns True (or nr of similar loaded packages) for a certain package
    if `return_package` == True then returns a reference to the module
    """
    i_res = sum([package_name in x for x in list(sys.modules.keys())])
    if return_package:
      if i_res > 0:
        return sys.modules[package_name]
      else:
        return None
    else:
      if as_bool:
        return i_res > 0
      else:
        return i_res

  def reset_seeds(self, seed=123, packages=['np', 'rn', 'tf', 'th']):
    """
    this method resets all possible random seeds in order to ensure
    reproducible results
    this method resets for:
        numpy, random, tensorflow, torch
    """
    _np, _rn, _tf, _th = None, None, None, None

    if 'np' in packages:
      _np = self.package_loader('numpy', return_package=True)

    if 'rn' in packages:
      _rn = self.package_loader('random', return_package=True)

    if 'tf' in packages:
      if 'tensorflow' in sys.modules:
        _tf = self.package_loader('tensorflow', return_package=True)

    if 'th' in packages:
      if 'torch' in sys.modules:
        _th = self.package_loader('torch', return_package=True)

    if _np is not None:
      self.P("Setting random seed {} for 'Numpy'".format(seed))
      _np.random.seed(seed)

    if _rn is not None:
      self.P("Setting random seed {} for 'random'".format(seed))
      _rn.seed(seed)

    if _tf is not None:
      self.P("Setting random seed {} for 'tensorflow'".format(seed))
      if _tf.__version__[0] == '2':
        _tf.random.set_seed(seed)
      else:
        _tf.set_random_seed(seed)

    if _th is not None:
      self.P("Setting random seed {} for 'torch'".format(seed))
      _th.manual_seed(seed)
    return
