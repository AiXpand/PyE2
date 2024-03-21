"""
Copyright 2019 Lummetry.AI (Knowledge Investment Group SRL). All Rights Reserved.


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

from functools import partial
from .base_logger import BaseLogger
from .logger_mixins import (
  _TimersMixin,
  _MatplotlibMixin,
  _ConfusionMatrixMixin,
  _HistogramMixin,
  _ComplexNumpyOperationsMixin,
  _DateTimeMixin,
  _DataFrameMixin,
  _GeneralSerializationMixin,
  _JSONSerializationMixin,
  _PickleSerializationMixin,
  _NLPMixin,
  _ComputerVisionMixin,
  _GridSearchMixin,
  _TimeseriesBenchmakerMixin,
  _VectorSpaceMixin,
  _DownloadMixin,
  _UploadMixin,
  _ProcessMixin,
  _MachineMixin,
  _GPUMixin,
  _ClassInstanceMixin,
  _ResourceSizeMixin,
  _PackageLoaderMixin,
  _PublicTFKerasMixin,
  _BasicTFKerasMixin,
  _AdvancedTFKerasMixin,
  _DeployModelsInProductionMixin,
  _FitDebugTFKerasMixin,
  _KerasCallbacksMixin,
  _TF2ModulesMixin,
  _BasicPyTorchMixin,
  _BetaInferenceMixin,
  _MultithreadingMixin,
  _UtilsMixin
)

class Logger(
  BaseLogger,
  _TimersMixin,
  _MatplotlibMixin,
  _ConfusionMatrixMixin,
  _HistogramMixin,
  _ComplexNumpyOperationsMixin,
  _DateTimeMixin,
  _DataFrameMixin,
  _GeneralSerializationMixin,
  _JSONSerializationMixin,
  _PickleSerializationMixin,
  _NLPMixin,
  _ComputerVisionMixin,
  _GridSearchMixin,
  _TimeseriesBenchmakerMixin,
  _VectorSpaceMixin,
  _DownloadMixin,
  _UploadMixin,
  _ProcessMixin,
  _MachineMixin,
  _GPUMixin,
  _ClassInstanceMixin,
  _ResourceSizeMixin,
  _PackageLoaderMixin,
  _PublicTFKerasMixin,
  _BasicTFKerasMixin,
  _AdvancedTFKerasMixin,
  _DeployModelsInProductionMixin,
  _FitDebugTFKerasMixin,
  _KerasCallbacksMixin,
  _TF2ModulesMixin,
  _BasicPyTorchMixin,
  _BetaInferenceMixin,
  _MultithreadingMixin,
  _UtilsMixin):

  def __init__(self, lib_name="",
               lib_ver="",
               config_file="",
               base_folder=None,
               app_folder=None,
               config_data={},
               show_time=True,
               config_file_encoding=None,
               no_folders_no_save=False,
               max_lines=None,
               HTML=False,
               DEBUG=True,
               data_config_subfolder=None,
               check_additional_configs=False,
               TF_KERAS=False,
               BENCHMARKER=False,
               dct_bp_params=None,
               default_color='n',
               ):

    super(Logger, self).__init__(
      lib_name=lib_name, lib_ver=lib_ver,
      config_file=config_file,
      base_folder=base_folder,
      app_folder=app_folder,
      show_time=show_time,
      config_data=config_data,
      config_file_encoding=config_file_encoding,
      no_folders_no_save=no_folders_no_save,
      max_lines=max_lines,
      HTML=HTML,
      DEBUG=DEBUG,
      data_config_subfolder=data_config_subfolder,
      check_additional_configs=check_additional_configs,
      default_color=default_color,
    )

    how_runs = ''
    if self.runs_from_ipython():
      how_runs = ' running in ipython'
    if self.runs_with_debugger():
      how_runs = ' running in debug mode'
    self.verbose_log(
        "  Python {}{}, Git branch: '{}', Conda: '{}'".format(
          self.python_version,
          how_runs,
          self.git_branch,
          self.conda_env,
        ), color='green'
      )

    self.verbose_log("  Os: {}".format(self.get_os_name()), color='g')
    self.verbose_log("  IP: {}".format(self.get_localhost_ip()), color='g')

    self.verbose_log('  Avail/Total RAM: {:.1f} GB / {:.1f} GB'.format(
      self.get_avail_memory(), self.get_machine_memory()
    ), color='green')

    if BENCHMARKER:
      dct_bp_params = dct_bp_params or {}
      self._setup_benchmarker(**dct_bp_params)

    if TF_KERAS:
      self.check_tf()

    self.cleanup_logs(archive_older_than_days=2)

    return

  def iP(self, str_msg, results=False, show_time=False, noprefix=False, color=None):
    if self.runs_from_ipython():
      return self._logger(
        str_msg,
        show=True, results=results, show_time=show_time,
        noprefix=noprefix, color=color
      )
    return

  def __repr__(self):
    # Get the name of the class
    class_name = self.__class__.__name__

    # Get public properties (those not starting with "_")
    public_properties = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    # Convert properties to a string representation
    properties_str = ", ".join(f"{k}={v!r}" for k, v in public_properties.items())

    return f"{class_name}({properties_str})"


class TestAnyLogger(BaseLogger, _DataFrameMixin):
  def __init__(self, lib_name="",
               lib_ver="",
               config_file="",
               base_folder=".",
               app_folder=".",
               show_time=True,
               config_file_encoding=None,
               no_folders_no_save=False,
               max_lines=None,
               HTML=False,
               DEBUG=True,
               data_folder_additional_configs=None):

    super(TestAnyLogger, self).__init__(
      lib_name=lib_name, lib_ver=lib_ver,
      config_file=config_file,
      base_folder=base_folder,
      app_folder=app_folder,
      show_time=show_time,
      config_file_encoding=config_file_encoding,
      no_folders_no_save=no_folders_no_save,
      max_lines=max_lines,
      HTML=HTML,
      DEBUG=DEBUG,
      data_folder_additional_configs=data_folder_additional_configs
    )

    return


SBLogger = partial(Logger, lib_name='tst', base_folder='.', app_folder='_local_cache')

if __name__ == '__main__':
  l = Logger('TEST', base_folder='Dropbox', app_folder='_libraries_testdata')
  l.P("All check", color='green')

  al = TestAnyLogger('TEST2', base_folder='Dropbox', app_folder='_libraries_testdata')
  al.P("All check TestAnyLogger", color='green')
