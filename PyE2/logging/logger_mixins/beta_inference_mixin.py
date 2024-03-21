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

class _BetaInferenceMixin(object):
  """
  Mixin for inference functionalities that are attached to `pye2.Logger` (onnx, trt)

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_BasicPyTorchMixin`:
    - self.load_pytorch_model

  * Obs: This mixin uses also attributes/methods of `_JSONSerializationMixin`:
    - self.load_models_json

  """

  def __init__(self):
    super(_BetaInferenceMixin, self).__init__()

    try:
      from .basic_pytorch_mixin import _BasicPyTorchMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _BetaInferenceMixin without having _BasicPyTorchMixin")

    try:
      from .json_serialization_mixin import _JSONSerializationMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _BetaInferenceMixin without having _JSONSerializationMixin")

    return

  ###############################
  ###                         ###
  ###  ONNX area              ###
  ###                         ###
  ###############################
  def load_onnx_model(self, model_name, full_path=False):
    import onnx
    import onnxruntime as ort

    if not model_name.endswith('.onnx'):
      model_name += '.onnx'

    if not full_path:
      model_full_path = os.path.join(self.get_models_folder(), model_name)
    else:
      model_full_path = model_name

    if not os.path.isfile(model_full_path):
      self.p('Provided path does not exists {}'.format(model_full_path))
      return

    self.p('Loading onnx model from: {}'.format(model_full_path))
    model = onnx.load(model_full_path)
    onnx.checker.check_model(model)
    onnx.helper.printable_graph(model.graph)

    ort_session = ort.InferenceSession(model_full_path)

    output_names = [node.name for node in model.graph.output]

    # TODO: review. this was needed for pytorch yolov3/yolov5
    l = []
    for x in output_names:
      try:
        int(x)
      except:
        l.append(x)
    output_names = l

    input_all = [node.name for node in model.graph.input]
    input_initializer = [node.name for node in model.graph.initializer]
    input_names = list(set(input_all) - set(input_initializer))

    return model, ort_session, input_names, output_names

  def saved_keras_to_onnx(self, model, onnx_name, folder='models'):
    import keras2onnx as k2o
    assert folder in [None, 'data', 'output', 'models']

    onnx_model = k2o.convert_keras(
      model=model,
      name=onnx_name
    )

    if not onnx_name.endswith('.onnx'):
      onnx_name += '.onnx'

    lfld = self.get_target_folder(target=folder)

    if folder is not None:
      path = os.path.join(lfld, onnx_name)
    else:
      path = onnx_name

    self.p('Saving keras model to onnx model at: {}'.format(path))
    k2o.save_model(onnx_model, path)
    self.p('Done saving onnx model')
    return

  def saved_pytorch_model_to_onnx(self, model_name,
                                  file_name,
                                  input_names=None,
                                  output_names=None,
                                  batch_size=None,
                                  input_height=None,
                                  input_width=None,
                                  input_channels=3,
                                  opset_version=11
                                  ):
    model = self.load_pytorch_model(model_name)
    path = self.pytorch_to_onnx(
      model=model,
      file_name=file_name,
      input_names=input_names,
      output_names=output_names,
      batch_size=batch_size,
      input_height=input_height,
      input_width=input_width,
      input_channels=input_channels,
      opset_version=opset_version
    )
    return path

  def pytorch_to_onnx(self, model,
                      file_name,
                      input_names=None,
                      output_names=None,
                      batch_size=None,
                      input_height=None,
                      input_width=None,
                      input_channels=3,
                      opset_version=11
                      ):
    import torch as th
    DEVICE = th.device('cuda:0' if th.cuda.is_available() else 'cpu')

    self.p('Converting {} to onnx'.format(model.__class__.__name__))
    assert (not input_height and not input_width) or (input_height and input_width)

    model.eval()
    EXT = '.pth.onnx'
    if not file_name.endswith(EXT):
      file_name = file_name + EXT

    input_shape, is_dynamic_shape, is_dynamic_batch = None, False, False
    if not batch_size and not input_height and not input_width:
      is_dynamic_shape = True
      input_shape = (1, input_channels, 1080, 1920)  # random numbera for input shape
    elif not batch_size:
      is_dynamic_batch = True
      input_shape = (
      1, input_channels, input_height, input_width)  # random number for batch_size. the batch_size will be made dynamic

    if not input_names:
      input_names = ['input']
    if not output_names:
      output_names = ['output']

    if is_dynamic_shape:
      dynamic_axes = {
        'input': {0: 'batch_size', 2: 'height', 3: 'width'},
        'output': {0: 'batch_size', 2: 'height', 3: 'width'}
      }  # adding names for better debugging
    elif is_dynamic_batch:
      dynamic_axes = {
        'input': {0: 'batch_size'},
        'output': {0: 'batch_size'}
      }
    else:
      dynamic_axes = None

    save_path = os.path.join(self.get_models_folder(), file_name)
    self.p('Saving model to: {}'.format(save_path[-50:]))

    th_inputs = th.zeros(*input_shape).to(DEVICE)
    th.onnx.export(
      model=model,
      args=th_inputs,
      f=save_path,
      input_names=input_names,
      output_names=output_names,
      dynamic_axes=dynamic_axes,
      opset_version=opset_version,
      verbose=True
    )

    self.p('Done converting pytorch model to onnx', show_time=True)
    return save_path

  ### end ONNX area

  ###############################
  ###                         ###
  ###  TRT  area              ###
  ###                         ###
  ###############################
  def load_tensorflow_trt_graph(self, graph_file, folder='models'):
    from ..nn.tf.utils import load_tf_graph, load_tf_graph_saved_model
    assert folder in [None, 'models']

    if not graph_file.endswith('.trt'):
      graph_file += '.trt'
    if folder is None:
      path = graph_file
    else:
      path = os.path.join(self.get_models_folder(), graph_file)

    if os.path.exists(path):
      cfg = self.load_models_json(graph_file + '.txt')
      lst_inputs = [v for k, v in cfg.items() if k.startswith('INPUT')]
      lst_outputs = [v for k, v in cfg.items() if k.startswith('OUTPUT')]
      try:
        self.p('Try loading graph is standard load graph method')
        trt_graph = load_tf_graph(log=self, pb_file=path, return_elements=lst_outputs)
      except:
        self.p('Could not load graph with standard load method.')
        self.p('Try loading graph from a saved model checkpoint')
        trt_graph = load_tf_graph_saved_model(log=self, pb_file=path)
      return trt_graph, lst_inputs, lst_outputs
    else:
      self.p('TRT graph not found on location: {}'.format(path))
    return

  def load_pytorch_trt_graph(self, graph_file, folder='models'):
    import torch as th
    from torch2trt import TRTModule
    assert folder in [None, 'models']

    if not graph_file.endswith('.trt'):
      graph_file += '.trt'
    if folder is None:
      path = graph_file
    else:
      path = os.path.join(self.get_models_folder(), graph_file)
    if os.path.exists(path):
      trt_graph = TRTModule()
      trt_graph.load_state_dict(th.load(path))
      # TODO: find a better way to obtain pytorch input/output names
      lst_inputs, lst_outputs = ['input'], ['output']
      return trt_graph, lst_inputs, lst_outputs
    else:
      self.p('TRT graph not found on location: {}'.format(path))
    return

  def pytorch_to_trt(self, model,
                     file_name,
                     input_height,
                     input_width,
                     input_channels,
                     max_batch_size=30):
    import torch as th
    from torch2trt import torch2trt

    DEVICE = th.device('cuda:0' if th.cuda.is_available() else 'cpu')

    EXT = '.pth.trt'
    if not file_name.endswith(EXT):
      file_name += EXT

    # create dummy input tensor
    th_x = th.ones((1, input_channels, input_height, input_width)).to(DEVICE)

    # convert to TensorRT feeding sample data as input
    # TODO: extend options for model converter
    model_trt = torch2trt(
      module=model,
      inputs=[th_x],
      max_batch_size=max_batch_size
    )

    path_model = os.path.join(self.get_models_folder(), file_name)
    th.save(model_trt.state_dict(), path_model)

    # load trt model for checking
    self.load_pytorch_trt_graph(graph_file=file_name)
    return file_name

  def tensorflow_graph_to_trt(self, graph_name,
                              input_names=None,
                              output_names=None,
                              folder='models',
                              max_batch_size=30
                              ):
    import tensorflow.compat.v1 as tf
    from ..nn.tf.utils import save_graph_to_file
    tf.disable_eager_execution()
    from tensorflow.python.compiler.tensorrt import trt_convert as trt
    EXT = '.trt'

    assert folder in [None, 'models']
    if folder:
      path_graph = self.get_models_file(graph_name)
      cfg = self.load_models_json(graph_name + '.txt')
      input_names = [v for k, v in cfg.items() if k.startswith('INPUT_')]
      output_names = [v for k, v in cfg.items() if k.startswith('OUTPUT_')]
      input_names = [x.split(':')[0] for x in input_names]
      output_names = [x.split(':')[0] for x in output_names]
    else:
      path_graph = graph_name
      assert input_names and output_names, 'Please provide input and output graph names'

    assert os.path.isfile(path_graph), 'Graph not found in {}'.format(path_graph)

    with tf.Session() as sess:
      # First deserialize the frozen graph
      with tf.gfile.GFile(path_graph, 'rb') as f:
        frozen_graph = tf.GraphDef()
        frozen_graph.ParseFromString(f.read())
      # endwith

      # Now you can create a TensorRT inference graph from frozen graph
      # TODO: extend options for model converter
      converter = trt.TrtGraphConverter(
        input_graph_def=frozen_graph,
        nodes_blacklist=output_names,
        max_batch_size=max_batch_size
      )  # output nodes
      trt_graph = converter.convert()

      trt_graph_name = graph_name + EXT

      save_graph_to_file(
        log=self,
        sess=sess,
        graph=trt_graph,
        pb_file=trt_graph_name,
        input_tensor_names=input_names,
        output_tensor_names=output_names
      )
    return trt_graph
  ### end TRT area