
import sys
import subprocess
import json
import shutil
import os
import glob
import r2pipe
import shutil

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
    # '4A6D890F-93C3-4B6D-A67D-5F2C4DCE347B', # Runtimesmm
]
use_ovmf_guids = [
   'A3FF0EF5-0C28-42F5-B544-8C7DE1E80014', #dexsmm
   '470CB248-E8AC-473C-BB4F-81069A1FE6FD', #faulttolerantwriteSmm
   '23A089B3-EED5-4AC5-B2AB-43E3298C2343', #variablesmm
#    '2D59F041-53A4-40D0-A6CD-844DC0DFEF17'  #s3smm save state  try to access sram while outside sram code
]
remove_ovmf_guid = [
    'E2EA6F47-E678-47FA-8C1B-02A03E825C6E'
]

utk_path = "./utk"
uefiextract_path = "./uefiextract"

def get_all_smm_modules(firmware):
    ret = []
    extract_command = [uefiextract_path,firmware,"all"]
    subprocess.run(extract_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    with open(firmware + ".report.txt") as f:
        for line in f.readlines():
            if "SMM module" in line or "SMM core" in line or "Combined SMM/DXE" in line:
                ret.append(line.split("|")[5].split(" ")[2].strip())
    return ret

def get_all_dxe_modules(firmware):
    ret = []
    extract_command = [uefiextract_path,firmware,"all"]
    subprocess.run(extract_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    with open(firmware + ".report.txt") as f:
        for line in f.readlines():
            if "DXE driver" in line:
                ret.append(line.split("|")[5].split(" ")[2].strip())
    return ret

def delete_smm_module(firmware,modules):
    for module in modules:
        print("delete " + module)
        utk_insert_command = [utk_path,firmware,"remove_pad",module,"save",firmware]
        subprocess.run(utk_insert_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)



def get_info(filename):
    with open(filename,"r") as f:
        return f.read()

def compose_body(dirname):
    info = get_info(os.path.join(dirname, "info.txt"))
    if "Type: Section" in info:
        if "Subtype: Compressed" in info:
            content = bytes()
            for file in os.listdir(dirname):
                if os.path.isdir(os.path.join(dirname, file)):
                    content += compose_body(os.path.join(dirname, file))
            return content
        else:
            header_f = open(os.path.join(dirname, "header.bin"),"rb")
            body_f = open(os.path.join(dirname, "body.bin"),"rb")

            header = header_f.read()
            body = body_f.read()

            content_len = len(header) + len(body)

            align_content_len = 4 - ( content_len % 4)

            total_len = content_len + align_content_len

            total_len_bytes = total_len.to_bytes(4, "little")
            header_bytearray = bytearray(header)
            header_bytearray[:3] = total_len_bytes[:-1]

            content = bytes(header_bytearray) + body

            content += (int(0).to_bytes(1, "little")) * align_content_len
            header_f.close()
            body_f.close()
            return content
    elif "Type: File" in info:
        header_f = open(os.path.join(dirname, "header.bin"),"rb")
        content = bytes()
        body = bytes()
        header = header_f.read()
        header_f.close()
        for file in os.listdir(dirname):
            if os.path.isdir(os.path.join(dirname, file)):
                body += compose_body(os.path.join(dirname, file))
        total_len = len(header) + len(body)
        total_len_bytes = total_len.to_bytes(4, "little")
        header_bytearray = bytearray(header)
        header_bytearray[20:23] = total_len_bytes[:-1]
        content = bytes(header_bytearray) + body
        return content
    return bytes()




def insert_smm_modules(ovmf_firmware,input_firmware,smm_modules):
    last_add = ""
    proj_path = os.path.dirname(ovmf_firmware)
    efis_path = os.path.join(proj_path,"efis")
    os.makedirs(efis_path, exist_ok=True)
    for module in smm_modules:
        print(module)
        for folder, subs, files in os.walk(input_firmware + ".dump"):
            if not os.path.isfile(os.path.join(folder,"info.txt")):
                continue
            with open(os.path.join(folder,"info.txt")) as f:
                content = f.read()
                if "File GUID: " + module in content and "Type: File" in content:
                    containt_compressed_section = False
                    for file in os.listdir(folder): 
                        if "Compressed section" in file:
                            containt_compressed_section = True
                    if containt_compressed_section:
                        selfcompose_bin = compose_body(folder)
                        module_filename = os.path.join(folder,"module_com.ffs")
                        outputf2 = open(module_filename, "wb")
                        outputf2.write(selfcompose_bin)
                        outputf2.close()
                    else:
                        module_filename = os.path.join(folder,"module.ffs")
                        outputf = open(module_filename, "wb")
                        headerf = open(os.path.join(folder,"header.bin"), "rb")
                        bodyf = open(os.path.join(folder,"body.bin"), "rb")
                        outputf.write(headerf.read()) + outputf.write(bodyf.read())
                        outputf.close()
                        headerf.close()
                        bodyf.close()

                        for folder, subs, files in os.walk(folder):
                            if os.path.isdir(folder):
                                if "PE32 image section" in folder:
                                    shutil.copyfile(os.path.join(folder,"body.bin"), os.path.join(efis_path,module+".efi"))

                    if last_add == "" : 
                        utk_insert_command = [utk_path,ovmf_firmware,"insert_after","VirtioRngDxe",module_filename,"save",ovmf_firmware]
                    else:
                        utk_insert_command = [utk_path,ovmf_firmware,"insert_after",last_add,module_filename,"save",ovmf_firmware]
                    subprocess.run(utk_insert_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("in total " + str(len(smm_modules)))


def clean(ovmf_firmware,input_firmware):
    os.remove(ovmf_firmware + ".report.txt")
    os.remove(ovmf_firmware + ".guids.csv")
    shutil.rmtree(ovmf_firmware + ".dump")

    os.remove(input_firmware + ".report.txt")
    os.remove(input_firmware + ".guids.csv")
    shutil.rmtree(input_firmware + ".dump")


if __name__ == "__main__":
    ovmf_path = sys.argv[2]
    vendor_firmware_path = sys.argv[1]
    proj_path = os.path.dirname(ovmf_path)
    vendor_smm_modules = get_all_smm_modules(vendor_firmware_path)
    ovmf_modules = get_all_smm_modules(ovmf_path)
    ovmf_dxe_modules = []
    ovmf_delete_modules = [x for x in ovmf_modules if x in vendor_smm_modules and x not in use_ovmf_guids]
    ovmf_delete_modules += remove_ovmf_guid
    delete_smm_module(ovmf_path,ovmf_delete_modules)
    vendor_smm_modules = [x for x in vendor_smm_modules if x not in unsupported_guids and x not in use_ovmf_guids and x not in ovmf_dxe_modules]
    insert_smm_modules(ovmf_path,vendor_firmware_path,vendor_smm_modules)
    with open(os.path.join(proj_path,"module.info"),"w") as f:
        for module in vendor_smm_modules:
            f.write(module + "\n")
    clean(vendor_firmware_path, ovmf_path)