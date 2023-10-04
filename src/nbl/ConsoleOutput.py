from ITest import *

class ExpectedFileAsDependencyTest(ITest):

    def __init__(self, test_name: str, config_json_filepaths, nabla_dir=None, print_warnings=True):
        super().__init__(test_name, config_json_filepaths, nabla_dir, print_warnings)


    # run a test for a single line of input for pathtracer
    def _impl_run_single_batch(self, executable:Path, command:list, config:dict, batch_data: dict) -> dict:
        expected_stdout_file = batch_data['dependencies'][0]
        with open(expected_stdout_file, "r") as file:
            expected = file.read().strip().replace('\r','') 
            #deleting \r from both to make sure neither are CRLF 

        console_output = subprocess.run(command, capture_output=True).stdout.decode().strip().replace('\r','')
        if(console_output != expected):
            return {
                'status': 'failed',
                'status_color': 'red',
            }
        else:
            return {
                'status': 'passed',
                'status_color': 'green',
            }
