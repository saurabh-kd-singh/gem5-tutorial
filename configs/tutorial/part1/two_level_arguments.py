import m5  # type: ignore
from m5.objects import *  # type: ignore
from caches import *

import argparse

parser = argparse.ArgumentParser(description='A simple system with 2-level cache.')
parser.add_argument("binary", default="", nargs="?", type=str,help="Path to the binary to execute.")
parser.add_argument("--l1i_size", help=f"L1 instruction cache size. Default: 16kB.")
parser.add_argument("--l1d_size",help="L1 data cache size. Default: Default: 64kB.")
parser.add_argument("--l2_size",help="L2 cache size. Default: 256kB.")

options = parser.parse_args()

system = System() # type: ignore

# Clock and voltage domain setup
system.clk_domain = SrcClockDomain() # type: ignore
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain() # type: ignore , VoltageDomain() is a SimObject that holds default voltage info

# Memory setup
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')] # type: ignore

#Create CPU
system.cpu = X86TimingSimpleCPU()() # type: ignore  # Added: Instantiate the CPU before using it 
system.cpu.icache = L1ICache(options)  # added options as parameter
system.cpu.dcache = L1DCache(options)  # added options as parameter

# Create memory bus
system.membus = SystemXBar() # type: ignore , This creates a System Crossbar interconnect a flexible, high-bandwidth communication channel

# Connect caches to the memory bus
# system.cpu.icache_port = system.membus.cpu_side_ports
# system.cpu.dcache_port = system.membus.cpu_side_ports
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

# L2 Cache
system.l2bus = L2XBar() # type: ignore
system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)
system.l2cache = L2Cache(options)  # added options as parameter
system.l2cache.connectCPUSideBus(system.l2bus)
system.membus = SystemXBar() # type: ignore
system.l2cache.connectMemSideBus(system.membus)

# Interrupts (for x86)
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# Connect system port
system.system_port = system.membus.cpu_side_ports

# Memory controller
system.mem_ctrl = MemCtrl() # type: ignore
system.mem_ctrl.dram = DDR3_1600_8x8() # type: ignore
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Binary path
# binary = 'tests/test-progs/hello/bin/x86/linux/hello'
binary = options.binary

# Workload setup (SE mode)
system.workload = SEWorkload.init_compatible(binary) # type: ignore

# Process setup
process = Process() # type: ignore
process.cmd = [binary] # This sets the command-line arguments for the process
system.cpu.workload = process
system.cpu.createThreads()

# Instantiate system
root = Root(full_system=False, system=system) # type: ignore
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()

print("Exiting @ tick {} because {}".format(m5.curTick(), exit_event.getCause()))
