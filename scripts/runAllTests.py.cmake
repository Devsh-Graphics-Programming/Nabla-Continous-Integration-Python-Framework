import sys
import os
os.chdir(os.path.dirname(__file__))

sys.path.append("@NBL_PYTHON_FRAMEWORK_MODULE_PATH_REL@") // relative path to Nabla Python Framework module, relocatable
sys.path.append("@NBL_TEST_TARGET_MODULE_PATH_REL@") // relative path to a test target interface module, relocatable

import test
test.main() // each test target implements its testing interface by overriding common one in Nabla Python Framework module