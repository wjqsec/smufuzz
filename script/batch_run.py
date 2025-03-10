import sys
import subprocess
import json
import shutil
import multiprocessing
import os
import psutil
import r2pipe
import signal
import time
fuzz_bin = "../LibAFL/target/release/qemu_smm"
compose_bin = "./compose.py"

# ovmf_bin = "../edk2/Build/OvmfX64/DEBUG_GCC5/FV/OVMF_CODE.fd"
# ovmf_vars = "../edk2/Build/OvmfX64/DEBUG_GCC5/FV/OVMF_VARS.fd"

ovmf_bin = "../edk2/Build/OvmfX64/RELEASE_GCC/FV/OVMF_CODE.fd"
ovmf_vars = "../edk2/Build/OvmfX64/RELEASE_GCC/FV/OVMF_VARS.fd"

prefix = "/home/w/hd/uefi_fuzz/experiments"

smm_fuzz_projs = [

[prefix + "/rsfuzzer/alien_r3/","Alienware 13 R3-alienware_13_r3_1.13.0.rom"],
[prefix + "/rsfuzzer/alien_x51/","Alienware X51 R3-dell_alienware_x51_r3"],
[prefix + "/rsfuzzer/asus_p453/","ASUS P453UJ-P453UJAS.311"],
[prefix + "/rsfuzzer/asus_un65u/","ASUS UN65U-UN65U-ASUS-0616.CAP"],
[prefix + "/rsfuzzer/game_x570/","X570 GAMING X-X570GX.36e"],
[prefix + "/rsfuzzer/game_z690/","Z690 GAMING X-Z690GAMINGX.F3"],
[prefix + "/rsfuzzer/hp_20/","HP 20-c000-hp-20-c000_versopm.bin"],
[prefix + "/rsfuzzer/hp_obelisk/","HP Obelisk 875-0821D.bin"],

[prefix + "/rsfuzzer/hp_z2/","HP Z2 Mini G4 -31A298"],
[prefix + "/rsfuzzer/hp_z440/","HP Z440-M60_0256.bin"],
[prefix + "/rsfuzzer/think_m700/","ThinkCentre M700-imagefw.rom"],
[prefix + "/rsfuzzer/think_p900/","Thinkstation P900-thinkpadp900.ROM"],
[prefix + "/rsfuzzer/think_x1/","Thinkpad X1 Fold-x1fold_version.FL1"],


[prefix + "/exp/acer_aspirea351/","acer_aspirea351.bin"],
[prefix + "/exp/acer_aspirer5371t/","acer_aspirer5371t.fd"],
[prefix + "/exp/asus_a407ub/","asus_a407ub.rom"],
[prefix + "/exp/asus_laptop_15_k509fa/","asus_laptop_15_k509fa.rom"],
[prefix + "/exp/asus_x509da/","asus_x509da.rom"],
[prefix + "/exp/dell_ispiron145410/","dell_ispiron145410.bin"],
[prefix + "/exp/dell_latitude7330/","dell_latitude7330.bin"],
[prefix + "/exp/dell_vostro7620/","dell_vostro7620.bin"],
[prefix + "/exp/dell_xps1595752in1/","dell_xps1595752in1.bin"],
[prefix + "/exp/dell_xps179700/","dell_xps179700.bin"],
[prefix + "/exp/gigabyte_aero15oled/","gigabyte_aero15oled.rom"],
[prefix + "/exp/gigabyte_x3plusr7/","gigabyte_x3plusr7.A0F"],
[prefix + "/exp/gigabyte_x9dt/","gigabyte_x9dt.B03"],

[prefix + "/exp/hp_8750000/","hp_8750000.bin"],
[prefix + "/exp/hp_a1yl6ua/","hp_a1yl6ua.bin"],
[prefix + "/exp/lenovo_ideapad_14alc7/","lenovo_ideapad_14alc7.bin"],
[prefix + "/exp/lenovo_thinkpadx1tablet1gen/","lenovo_thinkpadx1tablet1gen.FL1"],
[prefix + "/exp/lenovo_x12in1gen9/","lenovo_x12in1gen9.FL1"],
[prefix + "/exp/lenovo_x1extreme1gen/","lenovo_x1extreme1gen.FL1"],
[prefix + "/exp/razer_rz090196x/","razer_rz090196x.bin"],
[prefix + "/exp/razer_rz0903102/","razer_rz0903102.bin"],


[prefix + "/exp/microsoft_surface_go_wifi/","microsoft_surface_go_wifi.bin"],

[prefix + "/exp/msi_E15G3IMS/","msi_E15G3IMS.107"],
[prefix + "/exp/msi_E1585IMS/","msi_E1585IMS.318"],
[prefix + "/exp/msi_E15F4IBA/","msi_E15F4IBA.109"],


# [prefix + "/rsfuzzer/think_s30/","ThinkStation S30-IMAGEA2.bios"],  #broken
# [prefix + "/exp/hp_866c6ea/","hp_866c6ea.bin"],   #286 modules
# [prefix + "/exp/microsoft_surfacepro_10_for_business/","microsoft_surfacepro_10_for_business.bin"], # no smm modules

]
wait_f = []


def sigint_handler(signum, frame):
    if len(wait_f) == 0:
        exit(0)
    for f in wait_f:
        os.kill(f[0].pid, signal.SIGINT)
signal.signal(signal.SIGINT, sigint_handler)  

smm_fuzz_projs_tmp = []
for proj in smm_fuzz_projs:
    print("Fuzzing: " + proj[0])
    shutil.copyfile(ovmf_bin, os.path.join(proj[0], "OVMF_CODE.fd"))
    shutil.copyfile(ovmf_vars, os.path.join(proj[0], "OVMF_VARS.fd"))
    compose_command = ["python3", compose_bin, os.path.join(proj[0], proj[1]), os.path.join(proj[0], "OVMF_CODE.fd")]
    subprocess.call(compose_command, text=True)
    print("Embedding over")
    for i in range(1):
        smm_fuzz_projs_tmp.append([proj[0],proj[1], i+1])

while True:
    while len(wait_f) < psutil.cpu_count(logical = False) and len(smm_fuzz_projs_tmp) != 0:
        smm_fuzz_proj = smm_fuzz_projs_tmp.pop(0)
        tag = str(smm_fuzz_proj[2])
        os.makedirs(os.path.join(smm_fuzz_proj[0], tag), exist_ok=True)
        f = open(os.path.join(os.path.join(smm_fuzz_proj[0], tag),"fuzzer.log"), "w")
        fuzz_command = [fuzz_bin, "--proj",smm_fuzz_proj[0], "--tag" , tag, "fuzz","--fuzz-time","2h"]
        env_vars = os.environ.copy()
        env_vars["RUST_LOG"] = "info"
        result = subprocess.Popen(fuzz_command, stdout=f, stderr=f,env=env_vars)
        wait_f.append([result,smm_fuzz_proj])
    while True:
        time.sleep(3)
        to_exit = []
        to_terminate = []
        for f in wait_f:
            if f[0].poll() is not None:
                f[0].wait()
                to_exit.append(f)
                if f[0].returncode != 10:
                   smm_fuzz_projs_tmp.insert(0, f[1])  
            else:
                p = psutil.Process(f[0].pid)
                cpu_usage = p.cpu_percent(interval=10)
                if cpu_usage < 10:
                    f[0].kill()
                    to_terminate.append(f)
                    smm_fuzz_projs_tmp.insert(0, f[1])  
        for f in to_exit:
            wait_f.remove(f)
        for f in to_terminate:
            wait_f.remove(f)
        if len(smm_fuzz_projs_tmp) == 0 and len(wait_f) == 0:
            exit(0)
        if len(smm_fuzz_projs_tmp) != 0:
            break
