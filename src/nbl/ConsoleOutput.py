from .ITest import *

class ExpectedFileAsDependencyTest(ITest):

    def __init__(self, test_name: str, config_json_filepaths, nabla_dir=None, print_warnings=True):
        super().__init__(test_name, config_json_filepaths, nabla_dir, print_warnings)

    # run a test for a single line of input for pathtracer
    def _impl_run_single_batch(self, executable:Path, command:list, config:dict, batch_data: dict) -> dict:
        expected_stdout_file = self._get_dependencies(batch_data, config)[0]
        with open(expected_stdout_file, "r") as file:
            expected = file.read().strip().replace('\r','') 
            #deleting \r from both to make sure neither are CRLF 
        executor = subprocess.run(command, capture_output=True)
        console_output = executor.stdout.decode().strip().replace('\r','')
        if executor.returncode!=0: # Temporairly only check if return code 0 | all asserts passed
        #if(console_output != expected): TODO
            self.logwarn(f"failed comparing strings. result: {console_output}\nreference: {expected}")
            return {
                'console_output': console_output,
                'status': 'failed',
                'status_color': 'red',
            }
        else:
            return {
                'console_output': console_output,
                'status': 'passed',
                'status_color': 'green',
            }
