__author__ = 'welwu'

from argparse import ArgumentParser


def get_parser():
    _parser = ArgumentParser()
    _parser.add_argument('--loops', '-n', type=int, help='test times for every execute')
    _parser.add_argument('--rebuild', '-r', type=str, help='whether rebuild enviroment')
    _parser.add_argument('--recovery', '-c', type=str, help='whether recovery enviroment')
    required_arguments = _parser.add_argument_group('required arguments')
    required_arguments.add_argument('--baseline', '-b', type=str, help='software baseline under test', required=True)
    required_arguments.add_argument('--testset', '-t', type=str, help='testset config or remote', required=True)
    required_arguments.add_argument('--executor', '-e', type=str, help='use robot or pegasus',
                                    required=True, default='robot')
    required_arguments.add_argument('--config', '-g', type=str, help='config scf path')
    required_arguments.add_argument('--reporter', '-rep', type=str, help='need report result')
    required_arguments.add_argument('--pre_branch', '-p', type=str, help='such as CBTS18_MZ')
    required_arguments.add_argument('--HW_Release', '-hw', type=str, help='such as FSM4')
    return _parser

parser = get_parser()
