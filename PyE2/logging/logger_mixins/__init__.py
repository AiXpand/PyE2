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
import importlib
from .. import maybe_print

mixins_list = [
  ('advanced_tfkeras_mixin', '_AdvancedTFKerasMixin'),
  ('basic_pytorch_mixin', '_BasicPyTorchMixin'),
  ('basic_tfkeras_mixin', '_BasicTFKerasMixin'),
  ('beta_inference_mixin', '_BetaInferenceMixin'),
  ('class_instance_mixin', '_ClassInstanceMixin'),
  ('complex_numpy_operations_mixin', '_ComplexNumpyOperationsMixin'),
  ('computer_vision_mixin', '_ComputerVisionMixin'),
  ('confusion_matrix_mixin', '_ConfusionMatrixMixin'),
  ('dataframe_mixin', '_DataFrameMixin'),
  ('datetime_mixin', '_DateTimeMixin'),
  ('deploy_models_in_production_mixin', '_DeployModelsInProductionMixin'),
  ('download_mixin', '_DownloadMixin'),
  ('fit_debug_tfkeras_mixin', '_FitDebugTFKerasMixin'),
  ('gpu_mixin', '_GPUMixin'),
  ('grid_search_mixin', '_GridSearchMixin'),
  ('histogram_mixin', '_HistogramMixin'),
  ('keras_callbacks_mixin', '_KerasCallbacksMixin'),
  ('machine_mixin', '_MachineMixin'),
  ('matplotlib_mixin', '_MatplotlibMixin'),
  ('multithreading_mixin', '_MultithreadingMixin'),
  ('nlp_mixin', '_NLPMixin'),
  ('package_loader_mixin', '_PackageLoaderMixin'),
  ('process_mixin', '_ProcessMixin'),
  ('public_tfkeras_mixin', '_PublicTFKerasMixin'),
  ('resource_size_mixin', '_ResourceSizeMixin'),
  ('general_serialization_mixin', '_GeneralSerializationMixin'),
  ('json_serialization_mixin', '_JSONSerializationMixin'),
  ('pickle_serialization_mixin', '_PickleSerializationMixin'),
  ('tf2_modules_mixin', '_TF2ModulesMixin'),
  ('timers_mixin', '_TimersMixin'),
  ('timeseries_benchmarker_mixin', '_TimeseriesBenchmakerMixin'),
  ('upload_mixin', '_UploadMixin'),
  ('utils_mixin', '_UtilsMixin'),
  ('vector_space_mixin', '_VectorSpaceMixin'),
]
"""
The below code is used to import all mixins that are available and at the same time
report the unavailable mixins and the reason they are not available without raising any error.
It is equivalent to the following code:
```
try:
  from .timeseries_benchmarker_mixin import _TimeseriesBenchmakerMixin
except ModuleNotFoundError:
  _TimeseriesBenchmakerMixin = None
```
If you want to add a new mixin, you need to add it to the `mixins_list`.
"""
failed_imports = []
for mixin_module, mixin_name in mixins_list:
  try:
    module = importlib.import_module(f'.{mixin_module}', package=__package__)
    locals()[mixin_name] = getattr(module, mixin_name)
  except Exception as e:
    failed_imports.append((mixin_module, mixin_name, e))
    locals()[mixin_name] = None
  # endtry import
# endfor mixins_list
if len(failed_imports) > 0:
  failed_imports_str = "\n".join([
    f"{mixin_name} from .{mixin_module} ({reason})"
    for (mixin_module, mixin_name, reason) in failed_imports
  ])
  maybe_print(f"Warning! Failed to import the following mixins: \n{failed_imports_str}")
