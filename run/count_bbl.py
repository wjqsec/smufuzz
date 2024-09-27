#TODO write a description for this script
#@author
#@category _NEW_
#@keybinding
#@menupath
#@toolbar
#TODO Add User Code Here

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
print("\nall basic blocks:{}\n".format(len(bbs)))