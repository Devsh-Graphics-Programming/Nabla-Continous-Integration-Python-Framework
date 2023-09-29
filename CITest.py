import datetime
import os
import re
import subprocess
import filecmp
import json
import shlex
from pathlib import *

def get_git_revision_hash(repo_dir, branch = "HEAD") -> str:
    try:
        return subprocess.check_output(f'git -C "{repo_dir}" rev-parse {branch}').decode('ascii').strip()
    except Exception as ex:
        print("Exception occured when getting commit hash\n"+str(ex))
    return "error"

# Abstract class responsible for executing tests and saving their results
class CITest:
    
    # here are the methods that need to be implemented in a derived class
    # must override 
    def _impl_run_single_batch(self, executable:Path, command:list, config:dict) -> dict:
        pass


    # optional override
    def _impl_run_prerequisite_test(self):
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


    def _parse_config_json(self, config_json_filepath):
        # opens and parses config.json provided for the test
        input_commands = []
        config_json = {}
        with open(config_json_filepath) as json_file:
            config_json = json.load(json_file)
            for struct in config_json['data']:
                input_commands.append(struct['command'])
            self.log("Aggregating commands from " + config_json_filepath + ", obtained "+  str(input_commands))
        return input_commands, config_json
   

    def _change_working_dir(self, executable):
        self.working_dir = executable.parent.absolute()
        os.chdir(self.working_dir) 


    def _save_json(self, jsonFilename, dict, indent = 2):
        # turn a dictionary into json text and write to a file
        self.log("Saving json file to " + str(Path(jsonFilename).absolute()))
        with open(jsonFilename, "w+") as file:
            file.write(json.dumps(dict, indent = indent))

    
    def _split_command(self, command) -> list:
        # splits a shell command from a string into a list of arguments
        return shlex.split(command)


    def _get_executable_from_command(self, split_command : list) -> Path:
        # default behavior extracts the first argument from command 
        # but certain tests might want to return a different element
        return Path(split_command[0])


    def __try_run_prerequisite_test(self, summary) -> bool:
        dummy_run_result = self._impl_run_prerequisite_test()
        if dummy_run_result is not None:
            summary["dummy_run_status"] = 'passed' if dummy_run_result else 'failed' 
            if not dummy_run_result:
                self.logwarn("Dummy test failed. Aborting any further tests")
                return False
        return True


    def __init_summary_dict(self):
        summary = { 
            "commit": self.__get_commit_data(),
            "datetime": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
            "pass_status": 'pending',
            "identifier": self.test_name
        }
        self._impl_append_summary(summary)
        return summary


    def _validate_filepaths(self, executable: Path):
        if not executable.exists():
            self.logwarn(f'Executable at path "{executable}" does not exist')
            return False
        return True


    def run(self):
        summary = self.__init_summary_dict()
        test_profiles = []
        failures_global = 0
        ci_pass_status = self.__try_run_prerequisite_test(summary)
        summary["profiles"] = test_profiles

        if ci_pass_status:
            for index, config_json_filepath in enumerate(self.config_json_filepaths):
                self.log(f"Starting test {str(index+1)}/{len(self.config_json_filepaths)} with config file {config_json_filepath}")
                command_list, config = self._parse_config_json(config_json_filepath)
                path_to_change_cwd = Path(config_json_filepath).parent
                self._change_working_dir(path_to_change_cwd)
                profile_batch_results = []
                profile_result = {
                    'test_count': len(command_list),
                    'profile_index': index,
                    'results': profile_batch_results
                }                
                test_profiles.append(profile_result)

                for i, command in enumerate(command_list):
                    split_command = self._split_command(command)
                    executable = self._get_executable_from_command(split_command)
                    if self._validate_filepaths(executable):
                        try:
                            batch_result = self._impl_run_single_batch(executable, split_command, config)
                            self._change_working_dir(path_to_change_cwd) # reset cwd
                            batch_result['batch_index'] = i
                            if batch_result["status"] == 'failed':
                                summary["pass_status"] = "pending/failed"
                                failures_global = failures_global + 1
                                self.logwarn(f"Test failed for command {command} and profile {index}")
                            else:
                                self.log(f"Profile {index} command {i} finished with status {batch_result['status']}")

                            profile_batch_results.append(batch_result)
                            self._save_json(f"summary_{self.alphanumeric_only_test_name}.json",summary)

                        except Exception as ex:
                            print(f"[ERROR] Critical exception occured. Command: {command}\n Error: {str(ex.with_traceback())}")
                            ci_pass_status = False
       
        summary["failure_count"] = failures_global 
        summary["pass_status"] = 'passed' if ci_pass_status else 'failed'  
        self._save_json(f"summary_{self.alphanumeric_only_test_name}.json",summary)
        return ci_pass_status


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
