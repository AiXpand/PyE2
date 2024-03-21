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

import os
import sys
import json
import pickle
from io import BytesIO, TextIOWrapper

class _PublicTFKerasMixin(object):
  """
  Mixin for public tf keras functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_PickleSerializationMixin`:
    - self.load_pickle_from_models

  * Obs: This mixin uses also attributes/methods of `_JSONSerializationMixin`"
    - self.save_json
    - self.load_json
  """

  def __init__(self):
    super(_PublicTFKerasMixin, self).__init__()

    self.gpu_mem = None
    self.TF = False
    self.TF_VER = None
    self.TF_KERAS_VER = None
    self.KERAS = False
    self.KERAS_VER = None
    self.devices = {}
    return


  def _check_tf_avail(self):
    import tensorflow as tf
    try:
      self.TF_VER = tf.__version__
      found = True
      self.TF = True
    except:
      found = False
      self.TF = False
    return found

  def check_tf(self):
    import tensorflow as tf
    ret = 0
    if self._check_tf_avail():

      CHECK_GPUS = False
      tf_gpu = False
      is_eager = tf.executing_eagerly()
      # tf_gpu = tf.test.is_gpu_available(cuda_only=True)
      self._logger("Found TF {}. [eager mode {}]".format(
        self.TF_VER,
        "ON" if is_eager else "OFF"))
      ret = 2 if tf_gpu else 1
      if CHECK_GPUS:
        from tensorflow.python.client import device_lib
        local_device_protos = device_lib.list_local_devices()
        self.devices = {x.name: {'name': x.physical_device_desc,
                                 'mem': x.memory_limit, }
                        for x in local_device_protos}
        types = [x.device_type for x in local_device_protos]
        self.gpu_mem = []
        if 'GPU' in types:
          ret = 2
          for _dev in self.devices:
            if 'GPU' in _dev.upper():
              self._logger(" {}:".format(_dev[-5:]))
              self._logger("  Name: {}".format(self.devices[_dev]["name"]))
              self.gpu_mem.append(self.devices[_dev]["mem"] / (1024 ** 3))
              self._logger("  Mem:  {:.1f} GB".format(self.gpu_mem[-1]))
      try:
        self.TF_KERAS_VER = tf.keras.__version__
        self._logger("Found TF.Keras {}".format(self.TF_KERAS_VER))
      except:
        self.TF_KERAS_VER = None
        self._logger("No TF.Keras found.")

      if self._check_keras_avail():
        self._logger("Found Keras {}".format(self.KERAS_VER))
    else:
      self._logger("TF not found")
      self.TF = False
    return ret

  def get_gpu(self):
    res = []
    if self._check_tf_avail():
      self.TF = True
      from tensorflow.python.client import device_lib
      loc = device_lib.list_local_devices()
      res = [x.physical_device_desc for x in loc if x.device_type == 'GPU']
    return res

  def _check_keras_avail(self):
    try:
      found = True
      import keras
      self.KERAS_VER = keras.__version__
      self.KERAS = True
    except ImportError:
      found = False
      self.KERAS = False
    return found

  def is_tf2(self):
    if self._check_tf_avail():
      return self.TF_VER[0] == '2'
    else:
      return None

  def _block_tf2(self):
    import tensorflow as tf
    if self.is_tf2():
      if tf.executing_eagerly():
        self.P("WARNING: Called a function/method that uses TF1x approach (sessions, etc) in eager mode")
      else:
        self.P("WARNING: you are using tf2 with tf1 graphs - please ensure you use `tensorflow.compat.v1` - either `import tensorflow.compat.v1 as tf` or in calls")
    return

  def supress_tf_warnings(self):
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    return

  def supress_tf_warn(self):
    return self.supress_tf_warnings()

  def model_exists(self, model_file):
    """
    returns true if model_file (check both .pb or .h5) exists
    """
    exists = False
    for ext in ['', '.h5', '.pb']:
      fpath = os.path.join(self.get_models_folder(), model_file + ext)
      if os.path.isfile(fpath):
        exists = True
    if exists:
      self.P("Detected model {}.".format(fpath))
    else:
      self.P("Model {} NOT found.".format(model_file))
    return exists

  @staticmethod
  def get_keras_model_summary(model, full_info=False):
    if not full_info:
      # setup the environment
      old_stdout = sys.stdout
      sys.stdout = TextIOWrapper(BytesIO(), sys.stdout.encoding)
      # write to stdout or stdout.buffer
      model.summary()
      # get output
      sys.stdout.seek(0)  # jump to the start
      out = sys.stdout.read()  # read output
      # restore stdout
      sys.stdout.close()
      sys.stdout = old_stdout
    else:
      out = model.to_yaml()

    str_result = "Keras Neural Network Layout\n" + out
    return str_result

  def load_keras_model_def_and_weights(self, label, custom_objects=None, subfolder_path=None):
    import tensorflow as tf

    try:
      from custom_layers import CUSTOM_LAYERS
    except:
      try:
        from libraries.custom_layers import CUSTOM_LAYERS
      except:
        CUSTOM_LAYERS = {}

    load_folder = self.get_models_folder()
    if subfolder_path is not None:
      load_folder = os.path.join(load_folder, subfolder_path.lstrip('/'))

    if not os.path.exists(load_folder):
      self.P("Source load folder not found: '{}'".format(load_folder))
      return

    path_model_json = os.path.join(load_folder, label + '_model_def.json')
    path_model_weights = os.path.join(load_folder, label + '_weights.h5')

    if not os.path.exists(path_model_json):
      self.P("Model json file for '{}' does not exist in folder '...{}'".format(path_model_json, load_folder[-40:]))
      return

    if not os.path.exists(path_model_weights):
      self.P("Model weights file for '{}' does not exist in folder '...{}'".format(path_model_json, load_folder[-40:]))
      return

    self.P("Loading and reconstructing the model given label '{}' in folder '...{}'".format(
      label, load_folder[-40:]
    ))

    if custom_objects is None:
      custom_objects = {}
    for k, v in CUSTOM_LAYERS.items():
      custom_objects[k] = v

    model_json = json.dumps(self.load_json(path_model_json))

    try:
      model = tf.keras.models.model_from_json(model_json, custom_objects=custom_objects)
    except Exception:
      self.P("ERROR! There was a problem with `tf.keras.models.model_from_json`")
      return

    try:
      model.load_weights(path_model_weights)
    except Exception:
      self.P("ERROR! There was a problem with loading weights")
      return

    self.P("  Successfully loaded and reconstructed the model '{}'".format(label))
    return model

  def load_keras_model_weights(self, filename, model, layers):
    """
    load select 'layers' weights
    """
    assert len(layers) > 0, 'Unknown list of selected layers'
    file_name = os.path.join(self.get_models_folder(), filename + ".pkl")
    if not os.path.isfile(file_name):
      self.P("No weights file found")
      return False
    self.P("Loading weights for {} layers from {}...".format(len(layers), file_name))
    with open(file_name, 'rb') as f:
      w_dict = pickle.load(f)
    self.P("Loaded layers: {}".format(list(w_dict.keys())))
    for layer in layers:
      model.get_layer(layer).set_weights(w_dict[layer])
    self.P("Done loading weights.", show_time=True)
    return True

  def load_keras_model_from_weights(self, weights_file, config_file, custom_objects=None):
    import tensorflow as tf
    from_config = tf.keras.models.Model.from_config
    try:
      from custom_layers import CUSTOM_LAYERS
    except:
      from libraries.custom_layers import CUSTOM_LAYERS

    if custom_objects is None:
      custom_objects = {}
    for k, v in CUSTOM_LAYERS.items():
      custom_objects[k] = v

    self.P("Creating model from config and loading weights...")
    if weights_file[-3:] != '.h5':
      weights_file += '.h5'
    if config_file[-4:] != '.pkl':
      config_file += '.pkl'
    fn_cfg = os.path.join(self.get_models_folder(), config_file)
    fn_mdl = os.path.join(self.get_models_folder(), weights_file)
    if not os.path.isfile(fn_cfg):
      raise ValueError("Model config file not found: {}".format(fn_cfg))
    if not os.path.isfile(fn_mdl):
      raise ValueError("Model config file not found: {}".format(fn_mdl))
    dct_cfg = self.load_pickle_from_models(fn_cfg)
    model = from_config(dct_cfg, custom_objects=custom_objects)
    model.load_weights(fn_mdl)
    self.P("  Model created and weights loaded.")
    return model

  # custom_objects: dict with 'custom_name': custom_function
  def load_keras_model(self, model_name, custom_objects=None, DEBUG=True,
                       force_compile=True,
                       full_path=False,
                       subfolder_path=None):
    """
    Wrapper of `tf.keras.models.load_model`

    Parameters
    ----------

    model_name : str
      The name of the model that should be loaded.

    custom_objects : dict, optional
      Custom objects that should be loaded (besides the standard ones -
      from CUSTOM_LAYERS).
      The default is None.

    DEBUG : boolean, optional
      Specifies whether the logging is enabled
      The default is True.

    force_compile : boolean, optional
      `compile` param passed to tf.keras.models.load_model.
      The default is True.

    full_path : boolean, optional
      Specifies whether `model_name` is a full path or should be loaded
      from `_models` folder.
      The default is False.

    subfolder_path : str, optional
      A path relative to '_models' from where the model is loaded
      Default is None.
    """

    try:
      from custom_layers import CUSTOM_LAYERS
    except:
      try:
        from libraries.custom_layers import CUSTOM_LAYERS
      except:
        CUSTOM_LAYERS = {}

    if custom_objects is None:
      custom_objects = {}
    for k, v in CUSTOM_LAYERS.items():
      custom_objects[k] = v

    if model_name[-3:] != '.h5':
      model_name += '.h5'
    if DEBUG: self.verbose_log("  Trying to load {}...".format(model_name))

    if not full_path:
      model_folder = self.get_models_folder()
      if subfolder_path is not None:
        model_folder = os.path.join(model_folder, subfolder_path.lstrip('/'))

      model_full_path = os.path.join(model_folder, model_name)
    else:
      model_full_path = model_name

    if os.path.isfile(model_full_path):
      from tensorflow.keras.models import load_model

      if DEBUG: self.verbose_log("  Loading [...{}]".format(model_full_path[-40:]))
      model = load_model(model_full_path, custom_objects=custom_objects, compile=force_compile)
      if DEBUG: self.verbose_log("  Done loading [...{}]".format(model_full_path[-40:]), show_time=True)
    else:
      self.verbose_log("  File {} not found.".format(model_full_path))
      model = None
    return model

  def log_keras_model(self, model):
    self.verbose_log(self.get_keras_model_summary(model))
    return

  def show_model_summary(self, model):
    self.log_keras_model(model)
    return

  def load_graph_from_models(self, model_name, get_input_output=False):
    from libraries.nn.tf.utils import load_graph_from_models as _load
    return _load(
      log=self,
      model_name=model_name,
      get_input_output=get_input_output)

  @staticmethod
  def get_tensors_in_tf_graph(tf_graph):
    import tensorflow
    if isinstance(tf_graph, tensorflow.core.framework.graph_pb2.GraphDef):
      return [n.name for n in tf_graph.node]
    else:
      return [n.name for n in tf_graph.as_graph_def().node]
