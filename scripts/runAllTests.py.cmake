# Copyright (C) 2023 - DevSH Graphics Programming Sp. z O.O.

# "@EXECUTABLE_NAME@" target's test script, creates python environment for accessing 
# Nabla Python Framework module and runs the target's testing interface implementation

# Example of usage
# 1) runAllTests.py
#	- runs all profiles found, goes through all batches found in a profile being processed
# 2) runAllTests.py <profile path/index> [OPTIONAL] <batch index/range of batches> ... [OPTIONAL] <batch index/range of batches>
#	- runs given profile, if batch index (or range of batches) is given then it will process only the index of the batch (or the range)

import sys
import os

os.chdir(os.path.dirname(__file__))
sys.path.append("@NBL_PYTHON_FRAMEWORK_MODULE_PATH_REL@") // relative path to Nabla Python Framework module, relocatable
sys.path.append("@NBL_TEST_TARGET_MODULE_PATH_REL@") // relative path to a test target interface module, relocatable

import test
test.main() // each test target implements its testing interface by overriding common one in Nabla Python Framework module