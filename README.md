# smm_fuzz

code for S&P paper : SmuFuzz: Enable Deep System Management Mode Fuzzing in Fully Featured UEFI Runtime Environment

# Usage
Everything in a Docker image:
```
docker pull wjqsec555/smm_fuzz
```
Binary, source code, and scripts are included.

A usage video example:
https://drive.google.com/file/d/1r5bdZpmja37r3OW1Hn5T3_Ky4x8qzx_T/view?usp=drive_link

Native built:
```
git clone https://github.com/wjqsec/smufuzz.git
cd smufuzz
git clone https://github.com/wjqsec/LibAFL.git
git clone https://github.com/wjqsec/edk2.git
follow https://github.com/tianocore/tianocore.github.io/wiki/Getting-Started-with-EDK-II to compile edk2
cd LibAFL/fuzzers/qemu/qemu_smm
cargo build --release
refer to scripts to use
```
