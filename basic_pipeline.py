from m5.objects import *
from m5.util import *

# Setting up system configuration
def create_system(cpu_type, num_threads=1, issue_width=1, branch_prediction=None):
    sys = System()

    # Set up the clock and voltage domains
    sys.clk_domain = SrcClockDomain()
    sys.clk_domain.clock = '1GHz'
    sys.clk_domain.voltage_domain = VoltageDomain()

    # Setting up the memory bus
    sys.membus = SystemXBar()

    # Creating CPU based configuration
    if cpu_type == 'MinorCPU':
        sys_CPU = MinorCPU()
        sys_CPU.fetchWidth = 1
        sys_CPU.decodeWidth = 1
        sys_CPU.executeWidth = 1
        sys_CPU.memoryWidth = 1
        sys_CPU.commitWidth = 1
    elif cpu_type == 'DerivO3CPU':
        sys_CPU = DerivO3CPU()
        sys_CPU.fetchWidth = issue_width
        sys_CPU.decodeWidth = issue_width
        sys_CPU.issueWidth = issue_width
        sys_CPU.executeWidth = issue_width
        sys_CPU.commitWidth = issue_width
        sys_CPU.numThreads = num_threads
    else:
        raise ValueError("Unsupported CPU type")

    # Setting up branch predictors
    if branch_prediction:
        sys_CPU.branchPred = branch_prediction

    sys.sys_CPU = [sys_CPU]

    # Setting up memory system
    sys.mem_mode = 'timing'
    sys.mem_ranges = [AddrRange('512MB')]
    sys.mem_ctrl = DDR3_1600_8x8()
    sys.mem_ctrl.range = sys.mem_ranges[0]
    sys.mem_ctrl.port = sys.membus.master

    # Connecting the CPU to the memory bus
    sys.sys_CPU[0].icache_port = sys.membus.slave
    sys.sys_CPU[0].dcache_port = sys.membus.slave

    # Setting up interrupts and workload (binary program to run (hello_world.c))
    sys.sys_CPU[0].createInterruptController()
    binary = 'tests/test-progs/hello/bin/arm/linux/hello_world'  # Replace with your binary path
    sys.workload = SEWorkload.init_compatible(binary)
    sys.sys_CPU[0].workload = sys.workload
    sys.sys_CPU[0].createThreads()

    # Setting up the system port and connect the memory bus to the CPU
    sys.system_port = sys.membus.slave

    return sys


# Main function to run the simulation
def run_simulation(cpu_type, num_threads=1, issue_width=1, branch_prediction=None):
    sys = create_system(cpu_type, num_threads, issue_width, branch_prediction)

    # Set up root and instantiate the system
    root = Root(full_system=False, system=sys)
    m5.instantiate()

    print("Starting simulation...")
    exit_event = m5.simulate()

    # Collect stats
    print(f"Simulation ended at tick {m5.curTick()} because {exit_event.getCause()}")
    print("Collecting stats...")
    m5.stats.dump()
    m5.stats.reset()

    # Display key metrics
    ipc = sys.sys_CPU[0].commit.ipc
    instructions = sys.sys_CPU[0].commit.instructions
    cycles = sys.sys_CPU[0].numCycles
    print(f"Instructions committed: {instructions}")
    print(f"Instructions per Cycle: {ipc}")
    print(f"Total cycles: {cycles}")

    m5.stats.reset()
    m5.stats.dump()


# Run configurations for different parts of the assignment
if __name__ == "__main__":
    # Basic Pipeline Simulation
    print("Basic pipeline simulation...")
    run_simulation(cpu_type='MinorCPU')

    # Impact of Branch Prediction
    print("Simulation with branch prediction...")
    run_simulation(cpu_type='MinorCPU', branch_prediction=BiModeBP())

    # Multiple Issue Simulation (Superscalar)
    print("Superscalar configuration...")
    run_simulation(cpu_type='DerivO3CPU', issue_width=2)

    # Multithreading (SMT)
    print("SMT configuration with 2 threads...")
    run_simulation(cpu_type='DerivO3CPU', issue_width=2, num_threads=2)

