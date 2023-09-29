import os
import sys

def get_args():
    config_json_filepaths = []
    newArgv= []
    warnings = True
    nabla_dir = None
    for x in range(1,len(sys.argv)):
        arg = sys.argv[x]
        if arg == "-c":
            if len(sys.argv) > x+1 and not sys.argv[x+1].startswith("-"):
                config_json_filepaths.append(sys.argv[x+1])
                x = x+1
                continue
            else:
                print("When using -c to provide a path to config.json, actually provide the path")
                exit(2)
        elif arg == "-s":
            print("-s Disabling logging")
            warnings=False
            continue
        elif arg == "-n":
            if nabla_dir is None and len(sys.argv) > x+1:
                nabla_dir = sys.argv[x+1]
            else:
                print("-n [path to nabla] redefinition or no followig argument")
                exit(2)
        newArgv.append(sys.argv)
    return newArgv, config_json_filepaths, nabla_dir, warnings
