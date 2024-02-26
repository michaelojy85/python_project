import csv, os, shutil
import argparse
import paramiko
from paramiko.ssh_exception import SSHException, NoValidConnectionsError
from paramiko.client import SSHClient

class RemoteFileExtraction:
    def __init__(self):
        parser = self.add_args()
        args = parser.parse_args()

        self.ip = args.hostname
        if args.path == None and args.url == None:
            print("ERROR: At least url(-u) or path(-p) parameter must be called.")
            exit(1)
        else:
            self.path = args.path
            self.url = args.url

        self.sorting_enabled = args.sorting_enabled
        self.usr = 'root'
        self.pwd = 'amd123'
        self.local_path = f"""C:\\{args.folder}"""
        
        self.data_path = '/tmp/data' #if self.ip == 'ktm.cise' else '/tmp/data

    def add_args(self):
        parser = argparse.ArgumentParser(description='Simple script to extract zip files remotely.')
        parser.add_argument('-H', '--hostname', help='target sut hostname', required=True)
        parser.add_argument('-p', '--path', help='zip file name or file name + full path', default=None, required=False)
        parser.add_argument('-u', '--url', help='url on svm.cise', default=None, required=False)
        parser.add_argument('-f', '--folder', help='folder name', required=True)
        parser.add_argument('-sort', '--sorting_enabled', help='enable sorting csv file by bdf', action="store_true")
        return parser


    def open_connection(self):
        ####Start remote connection####
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.ip, username=self.usr, password=self.pwd, port=22, 
                disabled_algorithms=dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"]), 
                timeout=300, allow_agent=False, look_for_keys=False)
        remote_session = ssh.invoke_shell()
        remote_session.settimeout(2700)
        return ssh, remote_session


    def close_connection(self, ssh, sftp, session):
        ssh.close()
        sftp.close()
        session.close()


    def __sort_by_bdf(self, path):
        bdf_value = []
        for filename in os.listdir(path):
            if filename.endswith('.csv'):
                file_path = os.path.join(path, filename)
                
                with open(file_path) as csv_file:
                    for row in csv.DictReader(csv_file):
                        bdf = f"{row[' Bus']}_{row['Device']}_{row['Function']}"
                        break
                        
                if bdf not in bdf_value:
                    if not os.path.exists(os.path.join(path, bdf)):
                        os.mkdir(os.path.join(path, bdf))
                    bdf_value.append(bdf)
                
                if os.path.exists(file_path.replace('.csv', '.bin')):
                    shutil.move(file_path.replace('.csv', '.bin'), os.path.join(path, bdf))
                shutil.move(file_path, os.path.join(path, bdf))


    def content(self):
        pcie_margin_search_flag = False
        pcie_margin_4pt_flag = False
        xgmi_margin_search_flag = False
        xgmi_margin_4pt_flag = False

        ssh, remote_session = self.open_connection()

        sftp = ssh.open_sftp()
        sftp.put('extract_csv_file.py', '/tmp/extract_csv_file.py')

        cmd = f'python3 /tmp/extract_csv_file.py -o {self.data_path}'
        
        if self.path != None:
            cmd += f' -p {self.path}'
        else:
            cmd += f' -u {self.url}'

        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        if stdout:
            print(stdout.read())
        else:
            print(stderr.read())
            exit(1)

        if os.path.exists(self.local_path):
            shutil.rmtree(self.local_path)
        
        os.mkdir(self.local_path)
        # print(self.local_path)
            
        for filename in sftp.listdir(self.data_path):
            print(filename)
            sftp.get(
                     self.data_path + '/' + filename, 
                     os.path.join(self.local_path, filename)
                    )

        cmd = f'rm -rf /tmp/extract_csv_file.py {self.data_path}'
        stdin, stdout, sterr = ssh.exec_command(cmd)

        self.close_connection(ssh, sftp, remote_session)

        for filename in os.listdir(self.local_path):
            # print(filename)
            if filename.startswith('pcie_margin_output') or filename.startswith('pcie_margin_all'):
                pcie_margin_search_flag = True
            elif filename.startswith('pcie_4pt_margin') or filename.startswith('PCIeMarginResults_4PT'):
                pcie_margin_4pt_flag = True
            elif filename.startswith('xgmi_margin_all') or filename.startswith('LANE_MARGIN'):
                xgmi_margin_search_flag = True
            elif filename.startswith('xgmi_4PT_margin') or filename.startswith('PARALLEL_4PT'):
                xgmi_margin_4pt_flag = True

        if pcie_margin_search_flag:
            os.mkdir(os.path.join(self.local_path, 'pcie_margin_search'))

        if pcie_margin_4pt_flag:
            os.mkdir(os.path.join(self.local_path, 'pcie_margin_4pt'))

        if xgmi_margin_search_flag:
            os.mkdir(os.path.join(self.local_path, 'xgmi_margin_search'))
        
        if xgmi_margin_4pt_flag:
            os.mkdir(os.path.join(self.local_path, 'xgmi_margin_4pt'))

        for filename in os.listdir(self.local_path):
            if filename.startswith('pcie_margin_output') or filename.startswith('pcie_margin_all'):
                shutil.move(
                    os.path.join(self.local_path, filename), 
                    os.path.join(self.local_path, 'pcie_margin_search')
                )
            elif filename.startswith('pcie_4pt_margin') or filename.startswith('PCIeMarginResults_4PT'):
                shutil.move(
                    os.path.join(self.local_path, filename), 
                    os.path.join(self.local_path, 'pcie_margin_4pt')
                )
            elif filename.startswith('xgmi_margin_all') or filename.startswith('LANE_MARGIN'):
                shutil.move(
                    os.path.join(self.local_path, filename), 
                    os.path.join(self.local_path, 'xgmi_margin_search')
                )
            elif filename.startswith('xgmi_4PT_margin') or filename.startswith('PARALLEL_4PT'):
                shutil.move(
                    os.path.join(self.local_path, filename), 
                    os.path.join(self.local_path, 'xgmi_margin_4pt')
                )

        if self.sorting_enabled:
            for folder in ['pcie_margin_search', 'pcie_margin_4pt']:
                sorting_path = os.path.join(self.local_path, folder)
                if os.path.isdir(sorting_path):
                    self.__sort_by_bdf(sorting_path)

if __name__ == "__main__":
    rfe = RemoteFileExtraction()
    rfe.content()