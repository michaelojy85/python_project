import argparse
import json

class IdentifyDimmConfig:
    def __init__(self, file_path):
        self.file_path = file_path
        self.dimm_config = {}
        self.dimm = ''
    
    def identify_config(self):
        data = {}
        channel = {}

        with open(self.file_path, 'r') as f:
            f = f.readlines()
        
        for i in range(0, 12):
            for line in f:
                if f"Channel {i}" in line:
                    self.dimm_config[f"Channel {i}"] = {}

                if "\t\t\tDimm 0" in line:
                    channel["Dimm 0"] = data
                elif "\t\t\tDimm 1" in line:
                    channel["Dimm 1"] = data
                
                if "DIMM Mfg ID" in line or "DRAM Mfg ID" in line or \
                    "Die Revision" in line or "RCD Mfg ID" in line or \
                    "DIMM Serial Number" in line or "DIMM Part Number" in line or\
                    "DIMM Date Code" in line:
                    key = line.strip().split(':')[0].strip(' ')
                    value = line.strip().split(':')[-1]
                    data[key] = value.strip(' ')

                if "\t\t\tSize" in line or "\t\t\tRanks" in line:
                    key = line.strip().split(':')[0].strip(' ')
                    value = line.strip().split(':')[-1]
                    data[key] = value.strip(' ')                    
                
                if "\t\t\tBitRate" in line:
                    value = line.strip().split('=')[-1].strip(' ')
                    data["Data Rate"] = value.strip(' ')

                self.dimm_config[f"Channel {i}"] = channel

        print(json.dumps(self.dimm_config, indent=4))
        
        self.dimm, _ = list(channel.items())[0]


class matchODTfromAblLog(IdentifyDimmConfig):
    def __init__(self):
        parser = self.add_args()
        args = parser.parse_args()

        self.file_path = args.filename
        self.dimm_topology = []

        super().__init__(self.file_path)


    def add_args(self):
        parser = argparse.ArgumentParser(description='Simple script to extract zip files.')
        parser.add_argument('-f', '--filename', help='file name or file name + full path', required=True)
        return parser   


    def contents(self):

        with open(self.file_path, 'r') as f:
            f = f.readlines()

        for i in range(0, 12):
            for line in f:
                if f"Socket 1 Channel {i} Dimm 0" in line:
                    sliced_line = line.split(",")[0]
                    dimm_size = sliced_line.split(":")[-1].strip(" ")
                    if self.dimm_config[f"Channel {i}"][self.dimm]["Size"] == f"{dimm_size} GB":
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
            for line in f:
                matched += self.teminations_comparison(line, 0, terminations)
        elif self.dimm_topology[0] == "1-of-2":
            for line in f:
                matched += self.teminations_comparison(line, 1, terminations)
        elif self.dimm_topology[0] == "2-of-2":
            for line in f:
                matched += self.teminations_comparison(line, 0, terminations)
                matched += self.teminations_comparison(line, 1, terminations)

        print(f"No. of terminations settings matched: {matched}")

        for line in f:
            if "PptControl:" in line:
                if "0x0" not in line:
                    print(f"ERROR: PPT value mismatched: {line}")
            if "ADJUSTED PptControl:" in line:
                if "0x0" not in line:
                    print(f"ERROR: PPT value mismatched: {line}")


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

    def teminations_comparison(self, line, dimm_no, terminations):
        if f"DIMM {dimm_no} RttNomWr" in line:
            if str(terminations["RttNomWr"]) in line:
                return 1
            else:
                print(f"ERROR: Termination mismatched: {line}")
        elif f"DIMM {dimm_no} RttWr" in line:
            if str(terminations["RttWr"]) in line:
                return 1
            else:
                print(f"ERROR: Termination mismatched: {line}")
        elif f"DIMM {dimm_no} RttNomRd" in line:
            if str(terminations["RttNomRd"]) in line:
                 return 1
            else:
                print(f"ERROR: Termination mismatched: {line}")
        elif f"DIMM {dimm_no} RttPark" in line:
            if str(terminations["RttPark"]) in line:
                return 1
            else:
                print(f"ERROR: Termination mismatched: {line}")
        elif f"DIMM {dimm_no} DqsRttPark" in line:
            if str(terminations["DqsRttPark"]) in line:
                return 1
            else:
                print(f"ERROR: Termination mismatched: {line}")
        elif "POdtUp" in line:
            if str(terminations["POdtUp"]) in line:
                return 1
            else:
                print(f"ERROR: Termination mismatched: {line}")
        elif "POdtDn" in line:
            if str(terminations["POdtDn"]) in line:
                return 1
            else:
                print(f"ERROR: Termination mismatched: {line}")
        
        return 0


if __name__ == "__main__":
    matching = matchODTfromAblLog()
    matching.identify_config()
    matching.contents()            