# smm_fuzz

code for S&P paper : SmuFuzz: Enable Deep System Management Mode Fuzzing in Fully Featured UEFI Runtime Environment

# Usage
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
