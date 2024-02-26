import zipfile
import subprocess
import os, shutil
import argparse

from io import StringIO
from glob import glob


class Extract:

    def __init__(self):
        parser = self.add_args()
        args = parser.parse_args()

        self.file_path = args.path
        self.output_path = args.output
        self.url_path = args.url if args.url != None else ''
        self.temp = '/tmp/temp/'
        self.folders = ['pcie_margin_4pt', 'pcie_margin_preferred', 'xgmi_margin_4pt', 'xgmi_margining']


    def add_args(self):
        parser = argparse.ArgumentParser(description='Simple script to extract zip files.')
        parser.add_argument('-p', '--path', help='zip file name or file name + full path', required=False)
        parser.add_argument('-o', '--output', help='zip file name or file name + full path', required=True)
        parser.add_argument('-u', '--url', help='url on svm.cise', default=None, required=False)
        return parser
    

    def __transfer_zip_file_from_svm_cise(self, zipfile):
        path = '/var/log/scpi/' + self.url_path + zipfile
        print(path)
        
        cmd = f"sshpass -p 'amd123' scp -o StrictHostKeyChecking=no amd@svm.cise:{path} {self.temp}"
        
        output = subprocess.check_output(cmd, shell=True)
        
        self.__extract_files(os.path.join(self.temp))
    
    
    def __extract_files(self, path):
        zip_file_list = []

        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.zip'):
                    print(file)
                    zip_file_list.append(file)

            for zip_file in zip_file_list:
                with zipfile.ZipFile(os.path.join(path, zip_file), 'r') as zip:
                    files = zip.namelist()
                    for file in files:
                        filename, extension = os.path.splitext(file)

                        if extension == '.csv' or extension == '.bin':
                            zip.extract(file, self.temp)
        else:
            print(f"ERROR: Path does not exists: {path}")
            exit(1)
                    
                    
    def content(self):
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)
            print(f"File path created: {self.output_path}")

        if not os.path.exists(self.temp):
            os.mkdir(self.temp)
            print(f"File path created: {self.temp}")

        if self.url_path == '':
            if self.file_path.endswith('svm/') or self.file_path.endswith('svm'):
                for folder in self.folders:
                    if os.path.exists(os.path.join(self.file_path, folder)):
                        print(folder)
                        self.__extract_files(os.path.join(self.file_path, folder))
            else:
                self.__extract_files(os.path.join(self.file_path))
        else:
            cmd = f'sshpass -p \'amd123\'  ssh -o StrictHostKeyChecking=no amd@svm.cise ' + \
                  f'\"cd /var/log/scpi/{self.url_path};find  -type f -name \'*.zip\'\"'

            output = subprocess.check_output(cmd, shell=True)
            zip_files_list = output.decode('utf-8').split('\n')[:-1]

            for zip_file in zip_files_list:
                self.__transfer_zip_file_from_svm_cise(zip_file.lstrip('.'))
        
        for extension in ['.csv', '.bin']:
            for source in glob(self.temp + '**/*' + extension, recursive=True):
                print(source)
                shutil.copy(source, self.output_path) 
                
        shutil.rmtree(self.temp)


if __name__ == "__main__":
    extract = Extract()
    extract.content()