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

import os
import sys

from datetime import datetime as dt

class _TF2ModulesMixin(object):
  """
  Mixin for TF v2 modules functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_TF2ModulesMixin, self).__init__()

  def delete_module(self, label):
    return self.delete_tf2_module(label)

  def delete_tf2_module(self, label):
    import shutil
    save_folder = self.get_models_folder()
    module_folder = os.path.join(save_folder, label)
    if os.path.isdir(module_folder):
      shutil.rmtree(module_folder, ignore_errors=True)
      self.P("Remove {}".format(module_folder))
    return

  def save_module(self, module, label, unique_name=False, verbose=True):
    """
    Saves a tf.Module - wrapper for SaveTF2Module
    """
    return self.save_tf2_module(module=module, label=label, unique_name=unique_name, verbose=verbose)

  def save_tf2_module(self, module, label, unique_name=False, verbose=True):
    """
    Saves a tf.Module object

    Parameters
    ----------
    module : tf.Module
    label :  name of the model to be saved in `_models`
    unique_name : True if timestamp prefixing is required
    verbose : show info
    Returns
    -------
    None.

    """
    import tensorflow as tf
    save_folder = self.get_models_folder()
    file_prefix = ''
    if unique_name:
      file_prefix = dt.now().strftime("%Y%m%d_%H%M%S_")
    file_name = os.path.join(save_folder, file_prefix + label)
    # now stupid tf2 bug:
    if os.name == 'nt':
      file_name = file_name.replace('/', '\\')
    if verbose:
      self.verbose_log("Saving tf2 module [...{}]".format(file_name[-40:]))
    try:  # must try-except ... more tf2 bugs when saving
      tf.saved_model.save(module, file_name)
    except:
      _err = sys.exc_info()[0]
      self.P("ERROR: tf.saved_model.save failed: {}".format(_err))
    return

  def load_module(self, label, verbose=True):
    """
      Loads a tf.Module object for inference. Wrapper for LoadTF2Module
    """
    return self.load_tf2_module(label=label, verbose=verbose)

  def load_tf2_module(self, label, verbose=True):
    """
    Loads a tf.Module object for inference

    Parameters
    ----------
    label : name of the model from `_models` folder
    verbose : show info

    Returns
    -------
    mdl : tf.Module
    """
    import tensorflow as tf
    save_folder = self.get_models_folder()
    file_name = os.path.join(save_folder, label)
    mdl = tf.saved_model.load(file_name)
    self.P("Loaded tf2 module [...{}]".format(file_name[-40:]))
    return mdl
