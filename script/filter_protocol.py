
import sys
protocols_notfound = set()
protocols_found = set()
for i in range(len(sys.argv) - 1):
    with open(sys.argv[1+i],"r") as f:
        start_count = False
        for line in f.readlines():
            if "Evaluate SMM DEPEX for FFS" in line:
                start_count = True
                continue
            if "SmmCoreEntry end" in line or "Evaluate DXE DEPEX for FFS" in line:
                start_count = False
                continue
            if start_count == False:
                continue
            if "PUSH GUID" in line:
                if "TRUE" in line.split("=")[1]:
                    protocol_found = True
                else:
                    protocol_found = False
                protocol = line.split("(")[1].split(")")[0]
                if protocol_found:
                    protocols_found.add(protocol)
                else:
                    protocols_notfound.add(protocol)
for p in protocols_notfound - protocols_found:
    print(p)