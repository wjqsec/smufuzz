import sys
import subprocess
import json
import shutil
import os
import r2pipe

fuzz_bin = "../LibAFL/target/release/qemu_smm"
compose_bin = "./compose.py"

ovmf_bin = "../edk2/Build/OvmfX64/DEBUG_GCC5/FV/OVMF_CODE.fd"
ovmf_vars = "../edk2/Build/OvmfX64/DEBUG_GCC5/FV/OVMF_VARS.fd"

# ovmf_bin = "../edk2/Build/OvmfX64/RELEASE_GCC5/FV/OVMF_CODE.fd"
# ovmf_vars = "../edk2/Build/OvmfX64/RELEASE_GCC5/FV/OVMF_VARS.fd"
#alien_r3  alien_x51  asus_p453  asus_un65u  game_x570  game_z690  hp_20  hp_obelisk  hp_z2  hp_z440  think_m700  think_p900  think_s30  think_x1


smm_fuzz_projs = [
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/alien_r3/","Alienware 13 R3-alienware_13_r3_1.13.0.rom"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/alien_x51/","Alienware X51 R3-dell_alienware_x51_r3"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/asus_p453/","ASUS P453UJ-P453UJAS.311"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/asus_un65u/","ASUS UN65U-UN65U-ASUS-0616.CAP"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/game_x570/","X570 GAMING X-X570GX.36e"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/game_z690/","Z690 GAMING X-Z690GAMINGX.F3"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_20/","HP 20-c000-hp-20-c000_versopm.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_obelisk/","HP Obelisk 875-0821D.bin"],

["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_z2/","HP Z2 Mini G4 -31A298"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/hp_z440/","HP Z440-M60_0256.bin"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_m700/","ThinkCentre M700-imagefw.rom"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_p900/","Thinkstation P900-thinkpadp900.ROM"],
["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_x1/","Thinkpad X1 Fold-x1fold_version.FL1"]

# ["/home/w/hd/uefi_fuzz/experiments/rsfuzzer/think_s30/","ThinkStation S30-IMAGEA2.bios"],  #broken


# ["/home/w/hd/uefi_fuzz/experiments/exp/acer_aspirea351/","acer_aspirea351.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/acer_aspirer5371t/","acer_aspirer5371t.fd"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/asus_a407ub/","asus_a407ub.rom"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/asus_laptop_15_k509fa/","asus_laptop_15_k509fa.rom"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/asus_x509da/","asus_x509da.rom"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/dell_ispiron145410/","dell_ispiron145410.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/dell_latitude7330/","dell_latitude7330.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/dell_vostro7620/","dell_vostro7620.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/dell_xps1595752in1/","dell_xps1595752in1.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/dell_xps179700/","dell_xps179700.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/gigabyte_aero15oled/","gigabyte_aero15oled.rom"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/gigabyte_x3plusr7/","gigabyte_x3plusr7.A0F"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/gigabyte_x9dt/","gigabyte_x9dt.B03"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/hp_866c6ea/","hp_866c6ea.bin"],   #286 modules
# ["/home/w/hd/uefi_fuzz/experiments/exp/hp_8750000/","hp_8750000.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/hp_a1yl6ua/","hp_a1yl6ua.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/lenovo_ideapad_14alc7/","lenovo_ideapad_14alc7.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/lenovo_thinkpadx1tablet1gen/","lenovo_thinkpadx1tablet1gen.FL1"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/lenovo_x12in1gen9/"," lenovo_x12in1gen9.FL1"],  # cannot extract
# ["/home/w/hd/uefi_fuzz/experiments/exp/lenovo_x1extreme1gen/","lenovo_x1extreme1gen.FL1"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/razer_rz090196x/","razer_rz090196x.bin"],
# ["/home/w/hd/uefi_fuzz/experiments/exp/razer_rz0903102/"," razer_rz0903102.bin"],
]

wait_f = []

for smm_fuzz_proj in smm_fuzz_projs:
    print("Fuzzing: " + smm_fuzz_proj[0])
    shutil.copyfile(ovmf_bin, smm_fuzz_proj[0] + "OVMF_CODE.fd")
    shutil.copyfile(ovmf_vars, smm_fuzz_proj[0] + "OVMF_VARS.fd")
    compose_command = ["python3", compose_bin, smm_fuzz_proj[0] + smm_fuzz_proj[1], smm_fuzz_proj[0] + "OVMF_CODE.fd", smm_fuzz_proj[0] + "module.info"]
    subprocess.call(compose_command, text=True)
    print("Embedding over")

    f = open(smm_fuzz_proj[0] + "fuzzer.log", "w")
    fuzz_command = [fuzz_bin, "--proj",smm_fuzz_proj[0],"fuzz","--fuzz-time","20s" ]
    env_vars = os.environ.copy()
    env_vars["RUST_LOG"] = "info"
    result = subprocess.Popen(fuzz_command, stdout=f, stderr=f,env=env_vars )
    wait_f.append(result)

for f in wait_f:
    f.wait()



