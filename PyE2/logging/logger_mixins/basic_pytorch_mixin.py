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
from datetime import datetime as dt

class _BasicPyTorchMixin(object):
  """
  Mixin for basic pytorch functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_BasicPyTorchMixin, self).__init__()
    return

  def load_model_and_weights(
      self, model_class, weights_path, config_path,
      device='cuda', strict=True, return_config=False,
      config=None
  ):
    """
    Method for loading a model from a given class, with given configuration
    (either as a dictionary or as a .json) hyperparameters.
    Parameters
    ----------
    model_class - class extending torch.nn.Module, class of the given model
    weights_path - str, local path with the weights for the model
    config_path - str, local path with the json configuration
    device - torch.device, device on which to load the model
    strict - bool, will be used for load_state_dict()
    return_config - bool, whether to return the config as a dictionary
    config - dict, config that will be used as it is if provided

    Returns
    -------
    res - (torch.nn.Module, dict) if return_config else torch.nn.Module
    The instantiated model with the weights loaded and if required, the config dictionary of the model.
    """
    from torch import load
    try:
      model_kwargs = self.load_json(config_path) if config is None else config
      model = model_class(**model_kwargs)
      model.load_state_dict(
        load(weights_path, map_location=device),
        strict=strict
      )
      model.to(device)
    except Exception as e:
      raise e
    return (model, model_kwargs) if return_config else model

  def load_torch_weights(self, model_class, model_name, experiment_subfolder, device='cuda', strict=True):
    import torch as th
    model_files = os.listdir(
      os.path.join(
        self.get_models_folder(),
        experiment_subfolder
      )
    )
    model_files = [x for x in model_files if model_name in x]
    model_def_fn = [x for x in model_files if x.endswith('.json')][0]
    model_kwargs = self.load_json(
      os.path.join(
        self.get_models_folder(),
        experiment_subfolder,
        model_def_fn
      )
    )

    model = model_class(**model_kwargs)

    model_weights_fn = [x for x in model_files if x.endswith('.th') or x.endswith('.pth')][0]
    model.load_state_dict(th.load(
        os.path.join(self.get_models_folder(),experiment_subfolder, model_weights_fn),
        map_location=device
      ),
      strict=strict
    )

    return model

  def save_pytorch_model(self, model, label, use_prefix=False,
                         use_single_prefix=False,
                         DEBUG=True,
                         to_models=True):
    """
    DEPRECATED

    =========
    saves pytorch model to a file
    model : keras model
    label : name of the model
    use_prefix : will add date-time prefix if True (default False)
    use_single_prefix :  will use only one timestamp prefix for all saved models
    """
    import torch as th

    MDL_EXT = '.pth'
    file_prefix = ""
    if label == "":
      label = self.get_keras_model_desc(model)
    label = label.replace(">", "_")  # [:30]

    if use_single_prefix:
      file_prefix = self.file_prefix
    elif use_prefix:
      file_prefix = dt.now().strftime("%Y%m%d_%H%M%S_")

    save_folder = self.get_models_folder()
    if not to_models:
      save_folder = self.get_output_folder()

    file_name = os.path.join(save_folder, file_prefix + label)
    if file_name[-len(MDL_EXT):] == MDL_EXT:
      file_name = file_name[:-len(MDL_EXT)]
    if DEBUG:
      self.verbose_log("Saving [...{}]".format(file_name[-40:]))

    self.P("  Saving model...")
    save_file_name = file_name + MDL_EXT
    th.save(model, save_file_name)
    self.P("    Saved: {}".format(save_file_name))

    return file_name + MDL_EXT

  def load_pytorch_model(self, model_name, DEBUG=True, full_path=False):
    """
    DEPRECATED

    ===========
    Loads pytorch model

    Parameters
    ----------

    model_name : str
      The name of the model that should be loaded.

    DEBUG : boolean, optional
      Specifies whether the logging is enabled
      The default is True.

    full_path : boolean, optional
      Specifies whether `model_name` is a full path or should be loaded
      from `_models` folder.
      The default is False.
    """
    import torch as th

    name, ext = os.path.splitext(model_name)

    if ext != '.pth':
      model_name += '.pth'
    if DEBUG:
      self.verbose_log("  Trying to load {}...".format(model_name))

    if not full_path:
      model_full_path = os.path.join(self.get_models_folder(), model_name)
    else:
      model_full_path = model_name

    if os.path.isfile(model_full_path):
      if DEBUG: self.verbose_log("  Loading [...{}]".format(model_full_path[-40:]))
      model = th.load(model_full_path)
      if DEBUG: self.verbose_log("  Done loading [...{}]".format(model_full_path[-40:]), show_time=True)
    else:
      self.verbose_log("  File {} not found.".format(model_full_path))
      model = None
    return model
