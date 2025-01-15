
import sys
import subprocess
import json
import shutil
import os
import r2pipe


ovmf_guids = [
     "A47EE2D8-F60E-42FD-8E58-7BD65EE4C29B",
     "33FB3535-F15E-4C17-B303-5EB94595ECB6",
     "A3FF0EF5-0C28-42F5-B544-8C7DE1E80014",
     "2E7DB7A7-608E-4041-B45F-00359E0766C6",
     "23A089B3-EED5-4AC5-B2AB-43E3298C2343",
     "84EEA114-C6BE-4445-8F90-51D97863E363",
     "470CB248-E8AC-473C-BB4F-81069A1FE6FD",
     "E2EA6F47-E678-47FA-8C1B-02A03E825C6E",
     "60F343E3-2AE2-4AA7-B01E-BF9BD5C04A3B",
     "2D59F041-53A4-40D0-A6CD-844DC0DFEF17"
]
unsupported_guids = [
    # '991611CA-01AC-44A3-9C70-00F24A2B4AD9',   # dxe setvariable return fail  fixed by hooking setgetvariable
    # 'DAEC02CC-92C7-47DD-AE0D-498C204253AE',   # dxe setvariable return fail   fixed by hooking setgetvariable
    # 'D933DEDE-0260-4E76-A7D9-2F9F2440E5A5'    # get variable not found    fixed by hooking setgetvariable
    # 'F8F5C3C3-2EC9-4162-B649-EF41DFE615CD',     # smm getvariable not found  
    # 'FD93F9E1-3C73-46E0-B7B8-2BBA3F718F6C',     # cofig table getvariable not found?
    # '8F0B5301-C79B-44F1-8FD3-26D73E316700',   # hob guid not found, cmplog?
    # '91D211BF-37C2-495A-8DF7-9546BD2555C0',     # EFI_SM_MONITOR_INIT_PROTOCOL not found
]
use_ovmf_guids = [
   'A3FF0EF5-0C28-42F5-B544-8C7DE1E80014', #dexsmm
   '470CB248-E8AC-473C-BB4F-81069A1FE6FD', #faulttolerantwriteSmm
#    '2D59F041-53A4-40D0-A6CD-844DC0DFEF17'  #s3smm save state  try to access sram while outside sram code
 ]



utk_path = "/home/w/go/bin/utk"
uefiextract_path = "./uefiextract"
ghidra_analyzeheadless_path = "./ghidra_11.1.2_PUBLIC/support/analyzeHeadless"

ghidra_project_path = "/tmp/ghidra_project"

count_bbl_file_path = "/tmp/count_bbl.py"
count_bbl_src = '''
from ghidra.program.model.block import SimpleBlockIterator
from ghidra.program.model.block import BasicBlockModel
from ghidra.program.model.block import SimpleBlockModel
from ghidra.util.task import TaskMonitor

args = getScriptArgs()
bbm = SimpleBlockModel(currentProgram)
blocks = bbm.getCodeBlocks(TaskMonitor.DUMMY)
block = blocks.next()
bbs = set()
while block:
    bbs.add(block.getFirstStartAddress())
    block = blocks.next()
print("all basic blocks:{}".format(len(bbs)))
'''

def count_basic_blocks(exe_file):
    if os.path.exists(ghidra_project_path):
        shutil.rmtree(ghidra_project_path)
    os.mkdir(ghidra_project_path)
    ghidra_command = [ghidra_analyzeheadless_path, ghidra_project_path,"body.bin","-import", exe_file, "-postScript", count_bbl_file_path ]
    result = subprocess.run(ghidra_command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    if "all basic blocks:" in result.stdout:
        return int(result.stdout.split("all basic blocks:")[1].split("\n")[0])
    return 0

def find_dicts_with_key(obj,key_):
    results = []
    
    if isinstance(obj, dict):
        # Recursively check all values in the dictionary
        for key, value in obj.items():
            if key == key_:
                results.extend(value)

            results.extend(find_dicts_with_key(value,key_))
    
    elif isinstance(obj, list):
        # Recursively check all items in the list
        for item in obj:
            results.extend(find_dicts_with_key(item,key_))
    
    return results


def is_smm_module(module_desc):
    if isinstance(module_desc, dict):
        if "Type" in module_desc:
            # return module_desc["Type"] == "EFI_FV_FILETYPE_MM_CORE"
            return module_desc["Type"] == "EFI_FV_FILETYPE_MM" or module_desc["Type"] == "EFI_FV_FILETYPE_MM_CORE"
    return False

def get_all_smm_modules(firmware):
    utk_command = [utk_path,firmware,"json"]

    result = subprocess.run(utk_command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

    std_output = result.stdout

    parsed_data = json.loads(std_output)

    found =  find_dicts_with_key(parsed_data,"Files")

    modules = [x["Header"]["GUID"]["GUID"] for x in found if is_smm_module(x)]

    return modules

def delete_smm_module(firmware,modules):
    for module in modules:
        print("delete " + module)
        utk_insert_command = [utk_path,firmware,"remove_pad",module,"save",firmware]
        subprocess.run(utk_insert_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)

def insert_smm_modules(ovmf_firmware,input_firmware,smm_modules):
    total_bbl = 0
    last_add = ""
    for module in smm_modules:
        print("add " + module)
        
        utk_extract_command = [utk_path,input_firmware,"dump",module,"/tmp/smm.ffs"]
        subprocess.run(utk_extract_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)

        #efi_path_name = "/tmp/smm/" + module
        #uefiextract_command = [uefiextract_path,input_firmware,module,"-o",efi_path_name,"-m","body","-t","0x10"]
        #subprocess.run(uefiextract_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        
        #efi_file_name = efi_path_name + "/body.bin"
        #num_bbl = count_basic_blocks(efi_file_name)
        #total_bbl += num_bbl
        #print(num_bbl)
        if last_add == "" : 
            utk_insert_command = [utk_path,ovmf_firmware,"insert_after","VirtioRngDxe","/tmp/smm.ffs","save",ovmf_firmware]
        else:
            utk_insert_command = [utk_path,ovmf_firmware,"insert_after",last_add,"/tmp/smm.ffs","save",ovmf_firmware]
        last_add = module
        
        subprocess.run(utk_insert_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    print("total bbls {}".format(total_bbl))
def prepare_count_bbl_file():
    with open(count_bbl_file_path,"w") as f:
        f.write(count_bbl_src)



if not os.path.exists("/tmp/smm"):
    os.mkdir("/tmp/smm")

ovmf_path = sys.argv[2]
vendor_firmware_path = sys.argv[1]
prepare_count_bbl_file()
vendor_smm_modules = get_all_smm_modules(vendor_firmware_path)
ovmf_modules = get_all_smm_modules(ovmf_path)
ovmf_delete_modules = [x for x in ovmf_modules if x in vendor_smm_modules and x not in use_ovmf_guids]
delete_smm_module(ovmf_path,ovmf_delete_modules)
vendor_smm_modules = [x for x in vendor_smm_modules if x not in unsupported_guids and x not in use_ovmf_guids]
insert_smm_modules(ovmf_path,vendor_firmware_path,vendor_smm_modules)

