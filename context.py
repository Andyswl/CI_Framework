__author__ = 'welwu'

import os
import re
import platform
import sys
import ftplib
import SSHLibrary
import zipfile
import shutil
import paramiko

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from base.context import ExecutionContext
from base.utils import get_timestamp, logger
from conf import settings
from hran_execution import reporters, executors
from hran_execution.executors import RobotExecutor
from lib import cilib
from robot.libraries.BuiltIn import BuiltIn
import paramiko


os_name = platform.system().lower()
if 'windows' in os_name:
    CI_PATH = r'D:\cbts_bat\ta'
    CI_LOG = r'D:\cbts_bat\cilog'
    CONFIG_PATH = r"D:\hran_ta\config\Hangzhou"
elif 'linux' in os_name:
    CI_PATH = '/home/ute/cita/ta'
    CI_LOG = '/home/ute/cita/cilog'
else:
    raise EnvironmentError('Unknown operating system')

argumentfile = '_pybot_argumentfile.txt'


class CBTSRobotEexcutor(RobotExecutor):
    def __init__(self, variablefile, argumentfile, recovery_test=None, cireporter=None):
        super(CBTSRobotEexcutor, self).__init__(variablefile, argumentfile, recovery_test)
        self.listener = CBTSTestResultListener(cireporter)


class CBTSTestResultListener(executors._robot.TestResultListener):
    def __init__(self, cireporter):
        super(CBTSTestResultListener, self).__init__()
        self.ciReporter = cireporter

    """define action when a test case start."""
    def start_test(self, name, args):
        builtin = BuiltIn()
        self.ciReporter.report_case_start(name, args)

    """define action when a test case done."""
    def end_test(self, name, args):
        builtin = BuiltIn()
        self.ciReporter.report_case_end(name, args)


class CIContext(ExecutionContext):
    def __init__(self, args):
        self.baseline = args.baseline
        self.config = args.config
        self.test_set = args.testset
        self.logs_dir = self.get_logdir()
        self.argumentfile = None
        self.variablefile = None
        self.rebuild = args.rebuild
        self.recovery = args.recovery
        self.loops = int(args.loops) or 1
        self.current_loop = 0
        self.ciReporter = cilib.CiReporter(args.baseline, args.reporter)
        self.testset_content = self.get_testset()
        self.pre_branch = args.pre_branch
        self.HW_Release = args.HW_Release



    def set_build_status(self, verdict):
        """ Method to set build status """

    # Defines actions when a job build starts
    def __enter__(self):
        """Class context enter"""
        return self

    # Defines actions when a job build ends
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Class context exit"""

    @property
    def test_set_path(self):
        if self.test_set:
            if self.test_set == "remote":
                return os.path.join(self.logs_dir, 'remote.json')
            else:
                return os.path.join(self.logs_dir, self.test_set)
        else:
            raise BaseException("test_set is Null!")

    def get_executor(self):
        if self.variablefile and self.argumentfile:
            return CBTSRobotEexcutor(self.variablefile, self.argumentfile,
                                     recovery_test=None, cireporter=self.ciReporter)
        else:
            raise BaseException("varfile or argumentfile is Null")

    def get_reporter(self):
        console_reporter = reporters.LoggingTestReporter(logger=logger)

        return reporters.CompositeTestReporter(console_reporter, self.ciReporter)

    def get_logdir(self):
        return os.path.join(CI_LOG, '{}_{}_{}'.format(
            self.baseline, os.path.basename(self.test_set).split('.')[0], self.config))

    def get_testset(self):
        if self.test_set == "remote":
            try:
                self.ciReporter.get_testrun()
            except Exception:
                logger.error("No testset find")
                exit()
        else:
            src = os.path.join(CI_PATH, self.test_set)
            if os.path.exists(src):
                with open(src, 'rb') as fp:
                    content = fp.read()
                return content
            else:
                logger.error('No testset find {}'.format(self.test_set))
                exit()

    def get_varfile(self):
        var_file = os.path.join(self.logs_dir, 'var_file.yaml')
        with open(var_file, 'wb') as varfile:
            varfile.write('version : {}\n'.format(self.baseline))
            varfile.write('pre_branch : {}\n'.format(self.pre_branch))
            varfile.write('HW_Release : {}\n'.format(self.HW_Release))
            varfile.write('LOG_DIR : {}\n'.format(os.path.basename(self.logs_dir)))
        res = [var_file]
        var = os.path.join(CONFIG_PATH, self.config)
        if os.path.exists(var):
            if os.path.isfile(var):
                res.append(var)
            else:
                for r, d, fs in os.walk(var):
                    res.extend([os.path.join(r, f) for f in fs if (f.endswith('py') or f.endswith('yaml'))])
        else:
            logger.error('config {} not exist'.format(var))
        logger.info("Set var file  {}".format(res))
        return res

    def get_argfile(self):
        with open(os.path.join(CI_PATH, argumentfile), 'rb') as base_arg, \
                open(os.path.join(self.logs_dir, 'arg_file.txt'), 'wb') as argfile:
                    argfile.write(re.sub(r'(--outputdir ).*',
                                         '\\1{}\r'.format('\\\\'.join(self.logs_dir.split('\\'))), base_arg.read()))
        logger.info("Set arg file  {}".format(os.path.join(self.logs_dir, 'arg_file.txt')))
        return os.path.join(self.logs_dir, 'arg_file.txt')

    def validate_test_set(self):
        return True

    # Defines actions when a test suite start
    def before_tests_hook(self):
        if os.path.exists(self.logs_dir):
            self._move_logs()
        os.mkdir(self.logs_dir)
        self._log_testset()
        self.argumentfile = self.get_argfile()
        self.variablefile = self.get_varfile()


    # Defines actions when a test suite end
    def after_tests_hook(self):
        pass

    def _log_testset(self):
        with open(self.test_set_path, 'wb') as fp:
            fp.write(self.testset_content)

    def _log_environment_info(self):
        logger.info("Test set file path: %s" % self.test_set_path)
        logger.info("Tests:")
        logger.info(open(self.test_set_path).read())

    def _move_logs(self):
        if os.path.exists(self.logs_dir):
            new_logs_dir = self.logs_dir + '_%s' % get_timestamp()
            logger.info('Moving logs directory from %s to %s' % (self.logs_dir, new_logs_dir))
            shutil.move(self.logs_dir, new_logs_dir)

    def _remove_logs(self):
        for root, dirs, files in os.walk(CI_LOG):
            for name in files:
                if name.endswith(".zip"):
                    os.remove(os.path.join(root, name))

    def _copy_logs(self):
        if os.path.exists(self.logs_dir):
            old_dir = os.path.join('{}_{}_{}'.format(self.baseline,
                                                     os.path.basename(self.test_set).split('.')[0], self.config))
            os.chdir(CI_LOG)
            os.rename(old_dir, self.config)

    def _copy_logs_test(self):
        if os.path.exists(self.logs_dir):
            new_logs_dir = os.path.join(CI_LOG + "\\" + self.config)
            logger.info('Moving logs directory from %s to %s' % (self.logs_dir, new_logs_dir))
            shutil.copytree(self.logs_dir, new_logs_dir)

    def parse_cbts_package(self):
        res = re.match(r'^(CBTS[0-9a-z]+_[0-9a-z]+(_[a-z]+)*)_\d{4}_\d{6}_\d{6}(_\d+)*$', self.baseline, re.IGNORECASE)
        if res:
            return res.group(1)

    def copy_logs(self):
        os.chdir(CI_LOG)
        shutil.rmtree(self.config, True)
        logger.info('Copy logs to Logserver')
        log_name = os.path.basename(self.logs_dir)
        os.mkdir(os.path.join(self.logs_dir, 'runtime'))
        #ssh = SSHLibrary.SSHLibrary()
        os.chdir(self.logs_dir)
        logger.info('start')
        # ssh.open_connection(settings.LOG_FTP['ip'],timeout=180)
        # try:
        #     ssh.login(settings.LOG_FTP['usr'], settings.LOG_FTP['pass'])
        #     logger.info('mid')
        #     ssh.get_directory(r'{}/{}'.format(settings.LOG_FTP['LOG_ROOT'], log_name), recursive=True)
        #     ssh.execute_command(
        #         r"cd {}{};rm -rf {}".format(settings.LOG_FTP['ROOT_PATH'], settings.LOG_FTP['LOG_ROOT'], log_name))
        #     logger.info('end')
        # except Exception as e:
        #     logger.warn('Get btslog faild {}'.format(e.message))
        # ssh.close_connection()
        SSH = paramiko.SSHClient()
        SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            SSH.connect(settings.LOG_FTP['ip'], 22, settings.LOG_FTP['usr'], settings.LOG_FTP['pass'])
            SSH.exec_command(
                r"cd {}{};rm -rf {}".format(settings.LOG_FTP['ROOT_PATH'], settings.LOG_FTP['LOG_ROOT'], log_name),timeout=60)
        except Exception as e:
            print e
            print 'get log  Failed'
            exit()
        finally:
            SSH.close()

        timestamp = get_timestamp()
        logger.info('log path is ftp://%s%s/%s/%s_%s.zip' % (settings.LOG_FTP['ip'],settings.LOG_FTP['LOG_ROOT'],settings.LOG_FTP['LOG_MAP'].get(self.parse_cbts_package(), ""),log_name, timestamp))
        os.chdir(CI_LOG)
        with zipfile.ZipFile('{}_{}.zip'.format(log_name, timestamp), 'w', zipfile.ZIP_DEFLATED) as ziplog:
            for r, d, f in os.walk(self.logs_dir):
                for filename in f:
                    ziplog.write(os.path.join(r, filename))
        ftp = ftplib.FTP(settings.LOG_FTP['ip'], settings.LOG_FTP['usr'], settings.LOG_FTP['pass'])
        try:
            ftp.cwd(r'{}/{}'.format(settings.LOG_FTP['LOG_ROOT'],settings.LOG_FTP['LOG_MAP'].get(self.parse_cbts_package(), "")))
            with open('{}_{}.zip'.format(log_name, timestamp), "rb") as file_handler:
                ftp.storbinary('STOR {}_{}.zip'.format(log_name, timestamp), file_handler, 4096)
        except ftplib.error_perm as e:
            logger.warn('Put btslog faild {}'.format(e.message))
        ftp.close()
        #self._copy_logs()
        self._copy_logs_test()
        self._remove_logs()


