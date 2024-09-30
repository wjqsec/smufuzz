
import sys
import subprocess
import json
import shutil
import os
import r2pipe

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
            return module_desc["Type"] == "EFI_FV_FILETYPE_MM"
    return False

def extract_smm_modules(input_firmware):
    modules = []

    utk_command = [utk_path,input_firmware,"json"]

    result = subprocess.run(utk_command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

    # Capture the standard output
    std_output = result.stdout

    parsed_data = json.loads(std_output)

    all_smm_modules_found =  find_dicts_with_key(parsed_data,"Files")
    
    modules = [x["Header"]["GUID"]["GUID"] for x in all_smm_modules_found if is_smm_module(x)]


    return modules

def insert_smm_modules(ovmf_firmware,input_firmware,smm_modules):
    total_bbl = 0
    for module in smm_modules:
        

        utk_extract_command = [utk_path,input_firmware,"dump",module,"/tmp/smm.ffs"]
        subprocess.run(utk_extract_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)

        efi_path_name = "/tmp/smm/" + module
        uefiextract_command = [uefiextract_path,input_firmware,module,"-o",efi_path_name,"-m","body","-t","0x10"]
        subprocess.run(uefiextract_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)

        efi_file_name = efi_path_name + "/body.bin"
        num_bbl = count_basic_blocks(efi_file_name)
        total_bbl += num_bbl
        print(module,num_bbl)

        utk_insert_command = [utk_path,ovmf_firmware,"insert_after","TcgMorLockSmm","/tmp/smm.ffs","save",ovmf_firmware]
        subprocess.run(utk_insert_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    print("total bbls {}".format(total_bbl))
def prepare_count_bbl_file():
    with open(count_bbl_file_path,"w") as f:
        f.write(count_bbl_src)



if not os.path.exists("/tmp/smm"):
    os.mkdir("/tmp/smm")
prepare_count_bbl_file()
smm_modules = extract_smm_modules(sys.argv[1])
insert_smm_modules(sys.argv[2],sys.argv[1],smm_modules)

