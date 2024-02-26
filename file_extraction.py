import csv, os, shutil
import argparse
from zipfile import ZipFile
from pathlib import Path

class WinFileExtraction:
    def __init__(self):
        parser = self.add_args()
        args = parser.parse_args()
        
        self.base_dir = Path(os.path.dirname(os.path.realpath(__file__))).__str__()
        self.filename = args.filename
        self.output = args.output
        self.url_path = args.url if args.url != None else ''
        self.sorting_enabled = args.sorting_enabled
        
        
        self.network_path = "\\pngnasuni01\PNG_SCPI_CISE\crf\prod\scpi"
        self.folders = ['pcie_margin_4pt', 'pcie_margin_preferred', 'xgmi_margin_4pt', 'xgmi_margining']
        self.data_path = '/tmp/data' #if self.ip == 'ktm.cise' else '/tmp/data


    def add_args(self):
        parser = argparse.ArgumentParser(description='Simple script to extract zip files for pcie margining.')
        parser.add_argument('-f', '--filename', help='zip file name or file name + full path', default='default', required=False)
        parser.add_argument('-o', '--output', help='folder name', required=True)
        parser.add_argument('-u', '--url', help='url on svm.cise', default=None, required=False)
        parser.add_argument('-sort', '--sorting_enabled', help='enable sorting csv file by bdf', action="store_true")
        return parser
        
        
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
                
                if os.path.exists(file_path.replace('.csv', '.json')):
                    shutil.move(file_path.replace('.csv', '.json'), os.path.join(path, bdf))
                shutil.move(file_path, os.path.join(path, bdf))


    def __network_extract(self, src, dst):
        src = src.replace('/', os.sep)
        svm_path = f"\\{self.network_path}\{src}\svm"
        
        self.folders = [ f for f in os.listdir(svm_path) if f in self.folders]
        print(self.folders)
        
        for folder in self.folders: 
            path = f"{svm_path}\{folder}"
            
            if os.path.exists(path):
                zip_file_list = [ z for z in os.listdir(path) if z.endswith('.zip')]
                
                #print(zip_file_list)
                
                for zip_file in zip_file_list:
                    shutil.copy(
                            os.path.join(path, zip_file), 
                            os.path.join(self.base_dir, dst)
                    )

    def __extract_files(self, path, dst):
        zip_file_list = []

        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.zip'):
                    print(f"ZIP file detected: {file}")
                    zip_file_list.append(file)

            for zip_file in zip_file_list:
                with ZipFile(os.path.join(path, zip_file), 'r') as zip:
                    for file in zip.namelist():
                        if file.endswith('.csv') or file.endswith('.json'):
                            print(f"Extracting files on path: {file}")
                            zip.extract(file, dst)
        else:
            print(f"ERROR: Path does not exists: {path}")
            exit(1)
            
            
    def content(self):
        pcie_margin_search_flag = False
        pcie_margin_4pt_flag = False
        xgmi_margin_search_flag = False
        xgmi_margin_4pt_flag = False
        
        if os.path.exists(self.output):
            shutil.rmtree(self.output)
        os.mkdir(self.output)
        print(f"File path created: {self.output}")

        if not os.path.exists('temp'):
            os.mkdir('temp')
            print(f"File path created: temp")
            
        if self.url_path:
            self.__network_extract(self.url_path, 'temp')
        else:    
            shutil.unpack_archive(os.path.join(self.base_dir, self.filename), 'temp')     
        
        self.__extract_files('temp', 'temp')

        for path, subdirs, files in os.walk('temp'):
            for name in files:
                # print(os.path.join(path, name))
                if name.startswith('pcie_margin_output') or name.startswith('pcie_margin_all'):
                    pcie_margin_search_flag = True
                elif name.startswith('pcie_4pt_margin') or name.startswith('PCIeMarginResults_4PT'):
                    pcie_margin_4pt_flag = True
                elif name.startswith('xgmi_margin_all') or name.startswith('LANE_MARGIN'):
                    xgmi_margin_search_flag = True
                elif name.startswith('xgmi_4PT_margin') or name.startswith('PARALLEL_4PT'):
                    xgmi_margin_4pt_flag = True

        if pcie_margin_search_flag:
            os.mkdir(os.path.join(self.output, 'pcie_margin_search'))

        if pcie_margin_4pt_flag:
            os.mkdir(os.path.join(self.output, 'pcie_margin_4pt'))

        if xgmi_margin_search_flag:
            os.mkdir(os.path.join(self.output, 'xgmi_margin_search'))
        
        if xgmi_margin_4pt_flag:
            os.mkdir(os.path.join(self.output, 'xgmi_margin_4pt'))

        for path, subdirs, files in os.walk('temp'):
            for name in files:
                # print(os.path.join(path, name))
                if name.startswith('pcie_margin_output') or name.startswith('pcie_margin_all'):
                    shutil.move(
                        os.path.join(path, name), 
                        os.path.join(self.output, 'pcie_margin_search', name)
                    )
                elif name.startswith('pcie_4pt_margin') or name.startswith('PCIeMarginResults_4PT'):
                    shutil.move(
                        os.path.join(path, name), 
                        os.path.join(self.output, 'pcie_margin_4pt', name)
                    )
                elif name.startswith('xgmi_margin_all') or name.startswith('LANE_MARGIN'):
                    shutil.move(
                        os.path.join(path, name), 
                        os.path.join(self.output, 'xgmi_margin_search', name)
                    )
                elif name.startswith('xgmi_4PT_margin') or name.startswith('PARALLEL_4PT'):
                    shutil.move(
                        os.path.join(path, name), 
                        os.path.join(self.output, 'xgmi_margin_4pt', name)
                    )
                elif name.endswith('.zip'):
                    print(f"Deleting ZIP files: {name}")
                    os.remove(os.path.join(path, name))

        if self.sorting_enabled:
            for folder in ['pcie_margin_search', 'pcie_margin_4pt']:
                sorting_path = os.path.join(self.output, folder)
                if os.path.isdir(sorting_path):
                    self.__sort_by_bdf(sorting_path)    

        shutil.rmtree('temp')
        
        
if __name__ == "__main__":
    extract = WinFileExtraction()
    extract.content()