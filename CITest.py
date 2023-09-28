import datetime
import os
import re
import subprocess
import filecmp
import json
from pathlib import *

def get_git_revision_hash(repo_dir, branch = "HEAD") -> str:
    try:
        return subprocess.check_output(f'git -C "{repo_dir}" rev-parse {branch}').decode('ascii').strip()
    except Exception as ex:
        print("Exception occured when getting commit hash\n"+str(ex))
    return "error"

class CITest:
    
    # here are the methods that need to be implemented in a derived class
    # must override 
    def _impl_run_single(self, input_args) -> dict:
        pass

    # optional override
    def _impl_run_dummy_case(self):
        return None

    # optional override
    def _impl_append_summary(self, summary: dict):
        pass
    

    def _save_hash(self, hash, fileLocation):
        with open(fileLocation, "w+") as f:
            f.write(hash)
            self.log(f"Saved hash {hash} to file {fileLocation}")

    # compare if two files are equal, either by comparing if their hashes are  
    def _cmp_files(self, fileA, fileB, cmpByteByByte = False, cmpSavedHash = False, cmpSavedHashLocation = "", saveHash = False ):
        if cmpByteByByte:
            return filecmp.cmp(fileA, fileB)
        #compare git hashes
        executor1 = f'git hash-object {fileA}'
        executor2 = f'git hash-object {fileB}'
        hashA = subprocess.run(executor1, capture_output=True).stdout.decode().strip()
        hashB = subprocess.run(executor2, capture_output=True).stdout.decode().strip()
        res = hashA == hashB
        if res:
            if cmpSavedHash:
                if Path(cmpSavedHashLocation).is_file():
                    with open(cmpSavedHashLocation, "r") as f:
                        res = res and hashA == f.readline().strip()
                else:
                    self.logwarn(f"could not compare git hash of file '{hashA}' and '{hashB}' with a hash stored in a text file {cmpSavedHashLocation}. Text file storing hash does not exist")

        else:
            self.logwarn(f"files have different git commit hashes: '{fileA}', '{fileB}'")
        if res and cmpSavedHash and saveHash:
            self._save_hash(hashA, cmpSavedHashLocation)
        return res

    def logwarn(self, object):
        self.log(object, "[WARNING]")

    def log(self, object, hint = "[INFO]"):
        if self.print_warnings:
            print(hint + " " + str(object))
            # maybe write to file

    # constructor
    def __init__(self, 
                test_name : str,
                config_json_filepaths,
                nabla_dir = None, # leave none if you dont want commit info, else provide filepath to nabla dir
                print_warnings = True):
        self.test_name = test_name
        self.alphanumeric_only_test_name = re.sub(r"[^A-z0-9]+", "_", test_name).strip("_") #remove all non alphanumeric characters 
        self.config_json_filepaths = config_json_filepaths if config_json_filepaths is list else [config_json_filepaths]
        self.nabla_dir = nabla_dir
        self.print_warnings = print_warnings

    # opens and parses config.json provided for the test
    def _parse_config_json(self, config_json_filepath):
        with open(config_json_filepath) as json_file:
            self.config_json = json.load(json_file)
            self.input_commands = []
            for struct in self.config_json['data']:
                self.input_commands.append(struct['command'])
            self.log("Aggregating commands from " + config_json_filepath + ", obtained "+  str(self.input_commands))
   

    def _change_working_dir(self, executable):
        self.working_dir = executable.parent.absolute()
        os.chdir(self.working_dir) 


    def _validate_filepaths(self, executable):
        if not self.executable.exists():
            self.logwarn(f'Executable at path "{executable}" does not exist')
            return False
        if not self.input.exists():
            self.logwarn(f'Input file at path "{self.input}" does not exist')
            return False
        return True
    

    def _save_json(self, jsonFilename, dict):
        self.log("Saving json file to " + str(Path(jsonFilename).absolute()))
        with open(jsonFilename, "w") as file:
            file.write(json.dumps(dict, indent = 2))

    #TODO fix this 
    # def run(self):
    #     self._validate_filepaths()
    #     summary = { 
    #         "commit": self.__get_commit_data(),
    #         "datetime": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
    #         "pass_status": 'pending',
    #         "identifier": self.test_name
    #     }
    #     self._impl_append_summary(summary)
    #     test_results = []
    #     failures = 0
    #     ci_pass_status = True
    #     summary["results"] = test_results

    #     dummy_run_result = self._impl_run_dummy_case()
    #     if dummy_run_result is not None:
    #         summary["dummy_run_status"] = 'passed' if dummy_run_result else 'failed' 
    #         if not dummy_run_result:
    #             ci_pass_status = False
        
    #     if not ((dummy_run_result is not None) and (not ci_pass_status)):
    #         input_lines = self._get_input_lines()
    #         summary["num_of_tests"] = len(input_lines)
    #         testnum = 0
    #         for line in input_lines:
    #             try:
    #                 #update index of the test
    #                 testnum = testnum + 1

    #                 # run the test
    #                 result = self._impl_run_single(line)

    #                 # result is a dictionary, add additional fields
    #                 result["index"] = testnum 
    #                 is_failure = result["status"] == 'failed'

    #                 if is_failure:
    #                     ci_pass_status = False
    #                     summary["pass_status"] = "pending/failed"
    #                     failures = failures + 1
    #                     if self.print_warnings:
    #                         print(f"[WARN] input {line} is not passing the tests!")
    #                 else:
    #                     if self.print_warnings:
    #                         print(f"[INFO] input {line} PASSED")
    #                 test_results.append(result)
    #                 self._save_json(f"summary_{self.alphanumeric_only_test_name}.json",summary)
    #             except Exception as ex:
    #                 print(f"[ERROR] Critical exception occured during testing input {line}: {str(ex)}")
    #                 ci_pass_status = False
    #                 summary["critical_errors"] = f"{line}: {str(ex)}"
    #                 break
    #     summary["failure_count"] = failures 
    #     summary["pass_status"] = 'passed' if ci_pass_status else 'failed'  
    #     self._save_json(f"summary_{self.alphanumeric_only_test_name}.json",summary)
    #     return ci_pass_status


    def __get_commit_data(self):
        if self.nabla_dir is None:
            self.logwarn("Because nabla_dir was not assigned in CITest constructor, commit data will be empty")
            return {
                'hash' : "n/a",
                'author': "n/a",
                'date': "n/a",
                'name': "n/a"
            }
        lines = subprocess.check_output(f'git -C "{self.nabla_dir}" show').decode('ascii').strip().splitlines()
        return {
            'hash' : re.search(r"(?<=commit )\w+", lines[0]).group(),
            'author': lines[1],
            'date': lines[2],
            'name': lines[4].strip()
        }
