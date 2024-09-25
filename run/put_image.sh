sudo losetup --partscan  /dev/loop40 ./smmfuzz.img
sudo mount /dev/loop40p1 ./tmp_mount
sudo cp $1 ./tmp_mount/EFI/Boot/bootx64.efi
sudo umount ./tmp_mount
sudo losetup -d /dev/loop40
