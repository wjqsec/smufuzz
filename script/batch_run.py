import sys
import subprocess
import json
import shutil
import os
import r2pipe

fuzz_bin = "/home/w/hd/uefi_fuzz/fuzzer/LibAFL/target/release/qemu_smm"
compose_bin = "/home/w/hd/uefi_fuzz/fuzzer/run/compose.py"
ovmf_bin = "/home/w/hd/uefi_fuzz/fuzzer/edk2/Build/OvmfX64/RELEASE_GCC5/FV/OVMF_CODE.fd"
#alien_r3  alien_x51  asus_p453  asus_un65u  game_x570  game_z690  hp_20  hp_obelisk  hp_z2  hp_z440  think_m700  think_p900  think_s30  think_x1


smm_fuzz_projs = [
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/alien_r3/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/alien_r3/Alienware 13 R3-alienware_13_r3_1.13.0.rom"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/alien_x51/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/alien_x51/Alienware X51 R3-dell_alienware_x51_r3"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/asus_p453/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/asus_p453/ASUS P453UJ-P453UJAS.311"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/asus_un65u/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/asus_un65u/ASUS UN65U-UN65U-ASUS-0616.CAP"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/game_x570/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/game_x570/X570 GAMING X-X570GX.36e"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/game_z690/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/game_z690/Z690 GAMING X-Z690GAMINGX.F3"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_20/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_20/HP 20-c000-hp-20-c000_versopm.bin"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_obelisk/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_obelisk/HP Obelisk 875-0821D.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_z2/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_z2/HP Z2 Mini G4 -31A298"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_z440/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_z440/HP Z440-M60_0256.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_m700/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_m700/ThinkCentre M700-imagefw.rom"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_p900/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_p900/Thinkstation P900-thinkpadp900.ROM"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_s30/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_s30/ThinkStation S30-IMAGEA2.bios"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_x1/","/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_x1/Thinkpad X1 Fold-x1fold_version.FL1"]
]

for smm_fuzz_proj in smm_fuzz_projs:
    print("Fuzzing: " + smm_fuzz_proj[0])
    shutil.copyfile(ovmf_bin, smm_fuzz_proj[0] + "OVMF_CODE.fd")
    compose_command = ["python3", compose_bin, smm_fuzz_proj[1], smm_fuzz_proj[0] + "OVMF_CODE.fd", smm_fuzz_proj[0] + "module.info"]
    subprocess.call(compose_command, text=True)

wait_f = []
for smm_fuzz_dir in smm_fuzz_projs: 
    f = open(smm_fuzz_dir[0] + "fuzzer.log", "w")
    fuzz_command = [fuzz_bin, "--proj",smm_fuzz_dir[0],"fuzz","--fuzz-time","24h" ]
    env_vars = os.environ.copy()
    env_vars["RUST_LOG"] = "info"
    result = subprocess.Popen(fuzz_command, stdout=f, stderr=f,env=env_vars )
    wait_f.append(result)

for f in wait_f:
    f.wait()



