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

class _DeployModelsInProductionMixin(object):
  """
  Mixin for deployable models functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_DeployModelsInProductionMixin, self).__init__()

  def save_code(self, obj, name, folder):
    import cloudpickle
    info = sys.version_info
    sver = '_{}{}{}'.format(info.major, info.minor, info.micro)
    assert not any(char.isdigit() for char in name), "name must not contain numbers - {}".format(name)

    fn = os.path.join(folder, name + sver + '.dat')
    with open(fn, 'wb') as fh:
      cloudpickle.dump(obj, fh)
    self.P("Saved '{}'".format(fn))
    return

  def load_code(self, name, folder):
    import pickle
    import cloudpickle
    vmm = int(cloudpickle.__version__[:3].replace('.', ''))
    if vmm < 16:
      self.raise_error("You must have cloudpickle >= 1.6.0. Found {}".format(
        cloudpickle.__version__))
    info = sys.version_info
    sver = '_{}{}{}'.format(info.major, info.minor, info.micro)
    assert not any(char.isdigit() for char in name), "name must not contain numbers - {}".format(name)

    fn = os.path.join(folder, name + sver + '.dat')

    if not os.path.isfile(fn):
      fnhs = [x for x in os.listdir(folder) if name in x]
      raise ValueError('File {} not found. Avail files are: {}'.format(
        fn, fnhs))

    with open(fn, 'rb') as fh:
      data = pickle.load(fh)
    self.P("Loaded '{}'".format(fn))
    return data

  def _load_helper(self):
    helper = self.load_code('model_helper','libraries')
    return helper

  def load_deployed_library(self, filename, debug=False, **kwargs):
    """
    Loads a deployed library/module (.lib)

    Parameters
    ----------
    filename : str
      relative path of the file including the filename.

    Returns
    -------
    reference to the module.

    """
    _f = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[-1].lower()
    ext = ''.join([chr(x) for x in [46, 112, 121]]) if ext == '' else ext
    filename = _f + ext
    if not os.path.isfile(filename):
      filename = _f + '.lib'
      if not os.path.isfile(filename):
        raise ValueError("File '{}' not found!".format(filename))
      else:
        ext = '.lib'
    if ext != '.lib':
      if ext[-1] == 'y':
        import importlib
        module_name = filename.replace('/','.')[:-3]
        module_name = module_name.replace('\\','.')
        return importlib.import_module(module_name)
      else:
        raise ValueError("Deployed libraries must have '.lib' extension. Received: '{}'".format(
          filename))
    helper = self._load_helper()
    lib = helper.load_lib(self, filename, DEBUG=debug, **kwargs)
    return lib

  def save_deployable_library(self, filename, dest_folder=None, EXT='.lib'):
    """
    Saves a '.py' library/module in deploy format (.lib)

    Parameters
    ----------
    filename : str
      relative path of the file including the filename.

    dest_folder: str, defalut=None
      destination folder for the deployable library

    EXT: str, default='.lib'
      default deployable library extension


    Returns
    -------
    reference to the module.

    """
    EXT = '.lib'
    if not os.path.isfile(filename):
      raise ValueError("File '{}' not found!".format(filename))
    fn = os.path.splitext(filename)
    if fn[-1].lower() != '.py':
      raise ValueError("Source libraries must have '.py' extension. Received: '{}'".format(
        filename))
    src = filename
    if dest_folder is not None:
      fn_only = os.path.splitext(os.path.split(filename)[1])[0]
      dst = os.path.join(dest_folder, fn_only + EXT)
    else:
      dst = fn[0] + EXT
    self.P("Saving '{}'".format(dst))
    helper = self._load_helper()
    helper.save_lib(
      self,
      src_lib=src,
      dst_lib=dst
    )
    return

  def save_deploy_model(self, model, name, where='models'):
    """
    Saves a model for deployment

    Parameters
    ----------
    model : tf model
      the model object.
    name : str
      name of the model or full path to the output file
    where : str, optional
      'models' if `name` is a simple name or `fullpath` if full path is provided.
      The default is 'models'.

    Returns
    -------
    None.

    """
    assert where in ['models', 'fullpath']

    helper = self._load_helper()
    assert helper is not None

    if name[-3:] == '.h5':
      name = name[:-3]

    if where == 'models':
      model_file = os.path.join(self.get_models_folder(), name)
    else:
      model_file = name

    model_file += '.dat'

    helper.save_for_serving(
      log=self,
      model=model,
      deploy_model_path=model_file
    )
    return

  def load_deploy_model(self,
                        name,
                        where='models',
                        custom_objects=None,
                        DEBUG=False):
    """
    Loads a deployed model in production

    Parameters
    ----------
    name : str
      name (if in 'models' folder) or full path to the model
    where : str, optional
      either 'models' or 'fullpath'. The default is 'models'.

    Returns
    -------
    tf model

    """
    assert where in ['models', 'fullpath']
    import tensorflow as tf

    helper = self._load_helper()
    assert helper is not None

    if where == 'models':
      model_file = os.path.join(self.get_models_folder(), name)
    else:
      model_file = name

    if not os.path.isfile(model_file):
      raise ValueError("Model data not found '{}'".format(model_file))

    helper.load_for_serving(
      log=self,
      deploy_model_path=model_file,
      load_func=tf.keras.models.load_model,
      custom_objects=custom_objects,
      DEBUG=DEBUG,
    )

    return helper
