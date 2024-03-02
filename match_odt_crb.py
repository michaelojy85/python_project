import argparse
import numpy as np
import csv
import json, re

class IdentifyDimmConfig:
    def __init__(self, file_path):
        self.file_path = file_path
        self.dimm_config = {}
        self.dimms = ''
    
    def identify_config(self):
        collections = []
        channel = {}

        regexes = [
            "DIMM Mfg ID", "DRAM Mfg ID", "Die Revision",
            "RCD Mfg ID", "DIMM Serial Number", "DIMM Part Number",  
            "DIMM Date Code", "\t\t\tSize", "\t\t\tRanks", "BitRate"
        ]
        
        with open(self.file_path, 'r+') as f:
            f = f.readlines()
            
            for i in range(0, 12):
                for line in f:
                    if f"Channel {i}" in line:
                        self.dimm_config[f"Channel {i}"] = {}

            for k, v in self.dimm_config.items():
                for line in f:
                    if "\t\t\tDimm 0" in line:
                        self.dimm_config[k]['Dimm 0'] = {}
                    elif "\t\t\tDimm 1" in line:
                        self.dimm_config[k]['Dimm 1'] = {}

            for regex in regexes:
                data = []
                for line in f:
                    if regex in line:
                        if regex == "BitRate":
                            data.append(re.findall('= (\d+)', line.strip())[0])
                        else:
                            data.append(re.findall(': ([^)]*)', line.strip())[0])

                if regex == "BitRate" and len(self.dimm_config['Channel 0']) == 2:
                    collections += [data + data]
                elif len(data) > 12 and len(self.dimm_config['Channel 0']) == 1:
                    collections += [data[:12]]
                elif bool(data) ==False:
                    continue
                else:
                    collections += [data]

            if len(collections) != len(regexes):
                regexes.remove("Die Revision")

            collections = np.array(collections).T.tolist()

            for ch in range(0, 12):
                for k, v in self.dimm_config[f"Channel {ch}"].items(): # the basic way
                    for regex in regexes:
                        if regex in ("\t\t\tSize", "\t\t\tRanks"):
                            regex = regex.split()[0]
                        if regex == "BitRate":
                            regex = "DDR5 Frequency"
                        self.dimm_config[f"Channel {ch}"][k][regex] = ''

            d = 0 
            while d < len(collections):
                
                if len(self.dimm_config['Channel 0']) == 2:
                    ch = int(d / 2)
                
                    if d % 2 == 0:
                        for r in range(0, len(regexes)):
                            if regexes[r] in ("\t\t\tSize", "\t\t\tRanks"):
                                regexes[r] = regexes[r].split()[0]
                            if regexes[r] == "BitRate":
                                regexes[r] = "DDR5 Frequency"
                            self.dimm_config[f"Channel {ch}"]['Dimm 0'][regexes[r]] = collections[d][r]
                    else:
                        for r in range(0, len(regexes)):
                            if regexes[r] in ("\t\t\tSize", "\t\t\tRanks"):
                                regexes[r] = regexes[r].split()[0]
                            if regexes[r] == "BitRate":
                                regexes[r] = "DDR5 Frequency"
                            self.dimm_config[f"Channel {ch}"]['Dimm 1'][regexes[r]] = collections[d][r]
                else:
                    ch = d

                    for k in self.dimm_config['Channel 0'].keys():
                        dimm = k

                    for r in range(0, len(regexes)):
                        if regexes[r] in ("\t\t\tSize", "\t\t\tRanks"):
                            regexes[r] = regexes[r].split()[0]
                        if regexes[r] == "BitRate":
                            regexes[r] = "DDR5 Frequency"                           
                        self.dimm_config[f"Channel {ch}"][dimm][regexes[r]] = collections[d][r]
                
                d += 1

        print(json.dumps(self.dimm_config, indent=4))
        
        self.dimms = list(self.dimm_config[f"Channel 0"])


class matchODTfromAblLog(IdentifyDimmConfig):
    def __init__(self):
        parser = self.add_args()
        args = parser.parse_args()

        self.file_path = args.filename
        self.output = args.output
        self.dimm_topology = []

        super().__init__(self.file_path)


    def add_args(self):
        parser = argparse.ArgumentParser(description='Simple script to extract zip files.')
        parser.add_argument('-f', '--filename', help='file name or file name + full path', required=True)
        parser.add_argument('-o', '--output', help='output csv file', required=True)
        return parser   


    def contents(self):

        with open(self.file_path, 'r') as f:
            f = f.readlines()

        for i in range(0, 12):
            for line in f:
                if re.match(f"Socket 1 Channel {i} Dimm 0: (\d+),", line):
                    dimm_size = re.findall('Dimm 0: (\d+),', line)[0]
                    if self.dimm_config[f"Channel {i}"][self.dimms[0]]["Size"] == f"{dimm_size} GB":
                        self.dimm_topology.append("1-of-1")
            
            if bool(self.dimm_topology) == False:           
                if len(self.dimm_config[f"Channel {i}"]) == 1:
                    self.dimm_topology.append("1-of-2")
                elif len(self.dimm_config[f"Channel {i}"]) == 2:
                    self.dimm_topology.append("2-of-2")

            for d in self.dimm_config[f"Channel {i}"]:
                self.dimm_topology.append(
                        self.dimm_config[f"Channel {i}"][d]["Ranks"]
                    )
                self.dimm_topology.append(
                        self.dimm_config[f"Channel {i}"][d]["DIMM Mfg ID"]
                    )
        
        self.dimm_topology = list(dict.fromkeys(self.dimm_topology))

        if len(self.dimm_topology) != 3:
            print("ERROR in SPD reading. Please check your system configuration:")
            print(self.dimm_topology)
        else:
            print(
                  f"Topology     = {self.dimm_topology[0]}\n" +
                  f"Rank         = {self.dimm_topology[1]}\n" +
                  f"Manufacturer = {self.dimm_topology[2]}"
                  )
 
        terminations = self.tuned_terminations(self.dimm_topology)
        print(json.dumps(terminations, indent=4))    

        matched = 0
        
        if self.dimm_topology[0] == "1-of-1":
            pattern = r'(DIMM 0 )'
        elif self.dimm_topology[0] == "1-of-2":
            pattern = r'(DIMM 1 )'
        elif self.dimm_topology[0] == "2-of-2":
            pattern = r'(DIMM 0 |DIMM 1 )'
        
        indices = (
           "RttNomWr", "RttWr", f"RttNomRd", " RttPark", "DqsRttPark", "POdtUp", "POdtDn"
          )
                  
        for line in f:
            if re.search(pattern, line):
                matched += self.teminations_comparison(line, indices[:-2], terminations)
            else:
                matched += self.teminations_comparison(line, indices[-2:], terminations)
        


        for line in f:
            if "PptControl:" in line:
                if "0x0" not in line:
                    print(f"ERROR: PPT value mismatched: {line}")
            if "ADJUSTED PptControl:" in line:
                if "0x0" not in line:
                    print(f"ERROR: PPT value mismatched: {line}")

        print(f"No. of terminations settings matched: {matched}")

        with open(f'{self.output}.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'Channel', 'Dimm', 'Size', 'Ranks', 'DIMM Mfg ID',
                'DRAM Mfg ID', 'RCD Mfg ID', 'DIMM Serial Number',
                'DIMM Part Number', 'DIMM Date Code', 'DDR5 Frequency'             
                                ])
            for i in range(0, 12):
                    for dimm in self.dimms:
                        writer.writerow([
                            i,
                            dimm,
                            self.dimm_config[f'Channel {i}'][dimm]['Size'], 
                            self.dimm_config[f'Channel {i}'][dimm]['Ranks'], 
                            self.dimm_config[f'Channel {i}'][dimm]['DIMM Mfg ID'], 
                            self.dimm_config[f'Channel {i}'][dimm]['DRAM Mfg ID'], 
                            self.dimm_config[f'Channel {i}'][dimm]['RCD Mfg ID'], 
                            self.dimm_config[f'Channel {i}'][dimm]['DIMM Serial Number'],
                            self.dimm_config[f'Channel {i}'][dimm]['DIMM Part Number'], 
                            self.dimm_config[f'Channel {i}'][dimm]['DIMM Date Code'], 
                            self.dimm_config[f'Channel {i}'][dimm]['DDR5 Frequency'],                 
                        ])

    def tuned_terminations(self, topology):
        termination_settings = {
            "2-of-2" :  {
                "1" : {
                    "Micron" : {
                        "RttNomWr" : 120,
                        "RttNomRd" : 60,
                        "RttWr" : 80, 
                        "RttPark" : 34,
                        "DqsRttPark" : 48,
                        "POdtUp" : 48,
                        "POdtDn" : 0
                    },
                    "Samsung" : {
                        "RttNomWr" : 120,
                        "RttNomRd" : 60,
                        "RttWr" : 80, 
                        "RttPark" : 34,
                        "DqsRttPark" : 48,
                        "POdtUp" : 48,
                        "POdtDn" : 0
                    },
                    "SK Hynix" : {
                        "RttNomWr" : 120,
                        "RttNomRd" : 60,
                        "RttWr" : 80, 
                        "RttPark" : 34,
                        "DqsRttPark" : 48,
                        "POdtUp" : 48,
                        "POdtDn" : 0
                    },
                },  
                "2" : {
                    "Micron" : {
                        "RttNomWr" : 240,
                        "RttNomRd" : 240,
                        "RttWr" : 120, 
                        "RttPark" : 48,
                        "DqsRttPark" : 60,
                        "POdtUp" : 60,
                        "POdtDn" : 240
                    },
                    "Samsung" : {
                        "RttNomWr" : 240,
                        "RttNomRd" : 240,
                        "RttWr" : 120, 
                        "RttPark" : 48,
                        "DqsRttPark" : 60,
                        "POdtUp" : 60,
                        "POdtDn" : 240
                    },
                    "SK Hynix" : {
                        "RttNomWr" : 240,
                        "RttNomRd" : 240,
                        "RttWr" : 120, 
                        "RttPark" : 48,
                        "DqsRttPark" : 60,
                        "POdtUp" : 60,
                        "POdtDn" : 240
                    },
                }, 
            },
            "1-of-2" :  {
                "1" : {
                    "Micron" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 60, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 48,
                        "POdtDn" : 0
                    },
                    "Samsung" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 60, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 48,
                        "POdtDn" : 0
                    },
                    "SK Hynix" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 60, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 48,
                        "POdtDn" : 0
                    },
                },  
                "2" : {
                    "Micron" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 240, 
                        "RttPark" : 48,
                        "DqsRttPark" : 60,
                        "POdtUp" : 60,
                        "POdtDn" : 0
                    },
                    "Samsung" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 120, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 60,
                        "POdtDn" : 0
                    },
                    "SK Hynix" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 120, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 60,
                        "POdtDn" : 0
                    },
                },              
            },
            "1-of-1" :  {
                "1" : {
                    "Micron" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 60, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 48,
                        "POdtDn" : 0
                    },
                    "Samsung" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 60, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 48,
                        "POdtDn" : 0
                    },
                    "SK Hynix" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 60, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 48,
                        "POdtDn" : 0
                    },
                },  
                "2" : {
                    "Micron" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 120, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 60,
                        "POdtDn" : 0
                    },
                    "Samsung" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 120, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 60,
                        "POdtDn" : 0
                    },
                    "SK Hynix" : {
                        "RttNomWr" : 0,
                        "RttNomRd" : 0,
                        "RttWr" : 120, 
                        "RttPark" : 60,
                        "DqsRttPark" : 60,
                        "POdtUp" : 60,
                        "POdtDn" : 0
                    },
                },              
            }
        }

        return termination_settings[topology[0]][topology[1]][topology[2]]

    def teminations_comparison(self, line, indices, terminations):                        
        for index in indices:
            if index in line:
                if re.findall(str(terminations[index.lstrip(' ')]), line):
                    return 1
                else:
                    print(f"ERROR: Termination mismatched: {line}")
        else: 
            return 0


if __name__ == "__main__":
    matching = matchODTfromAblLog()
    matching.identify_config()
    matching.contents()            