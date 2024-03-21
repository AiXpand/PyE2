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

class _KerasCallbacksMixin(object):
  """
  Mixin for keras callbacks functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_BasicTFKerasMixin`:
    - self.TF
  """

  def __init__(self):
    super(_KerasCallbacksMixin, self).__init__()
    try:
      from .basic_tfkeras_mixin import _BasicTFKerasMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _KerasCallbacksMixin without having _BasicTFKerasMixin")

    self._tensorboard_dir = None
    return

  def get_keras_lr_callback(self, monitor='loss', patience=3, factor=0.1,
                            use_tf_keras=True):
    import tensorflow as tf
    if use_tf_keras:
      assert self.TF
      cb = tf.keras.callbacks.ReduceLROnPlateau(monitor=monitor, patience=patience, factor=factor)
    else:
      # assert self.KERAS
      from keras.callbacks import ReduceLROnPlateau
      cb = ReduceLROnPlateau(monitor=monitor, patience=patience, factor=factor)
    return cb

  def get_keras_checkpoint_callback(self, model_name='model',
                                    monitor='loss', mode='auto',
                                    period=1, use_tf_keras=True, save_best_only=False):
    import tensorflow as tf
    dict_abbrv = {'val_loss': 'ValL', 'loss': 'L', 'K_rec': 'RECA',
                  'K_pre': 'PREC', 'K_f2': 'F2SC',
                  'K_r2': 'RSQ', 'val_K_pre': 'ValP', 'val_K_rec': 'ValR'}
    try:
      abbrv = dict_abbrv[monitor]
    except:
      abbrv = monitor[:3]

    if save_best_only:
      file_path = model_name + '_best_{}'.format(monitor) + ".h5"
    else:
      file_path = model_name + '_tk_E{epoch:02d}_' + abbrv + "{" + monitor + ":.6f}" + ".h5"

    file_path = self.file_prefix + '_' + file_path

    if use_tf_keras:
      assert self.TF

      self.verbose_log("Creating tf.keras chekpoint callback...")
      file_path = os.path.join(self.get_models_folder(), file_path)
      cb = tf.keras.callbacks.ModelCheckpoint(
        filepath=file_path,
        monitor=monitor,
        verbose=0,
        save_best_only=save_best_only,
        save_weights_only=False,
        mode=mode,
        period=period
      )
    else:
      # assert self.KERAS
      from keras.callbacks import ModelCheckpoint
      self.verbose_log("Creating keras chekpoint callback...")
      file_path = os.path.join(self.get_models_folder(), file_path)
      cb = ModelCheckpoint(
        filepath=file_path,
        monitor=monitor,
        verbose=0,
        save_best_only=save_best_only,
        save_weights_only=False,
        mode=mode,
        period=period
      )

    return cb

  def get_keras_tensorboard_callback(self, use_tf_keras=True):
    """
    """
    import tensorflow as tf
    if use_tf_keras:
      assert self.TF == True

      self.verbose_log("Creating tf.keras tensorboard callback...")
      self._tensorboard_dir = os.path.join(self.get_base_folder(), '_tf');
      if not os.path.isdir(self._tensorboard_dir):
        os.makedirs(self._tensorboard_dir)
      cb_tboard = tf.keras.callbacks.TensorBoard(
        log_dir=self._tensorboard_dir,
        histogram_freq=1,
        write_graph=True,
        write_images=True
      )
    else:
      from keras.callbacks import TensorBoard
      # assert self.KERAS == True
      self.verbose_log("Creating Keras tensorboard callback...")
      self._tensorboard_dir = os.path.join(self.get_base_folder(), '_tf');
      if not os.path.isdir(self._tensorboard_dir):
        os.makedirs(self._tensorboard_dir)
      cb_tboard = TensorBoard(
        log_dir=self._tensorboard_dir,
        histogram_freq=1,
        write_graph=True,
        write_images=True
      )
    return cb_tboard

