import subprocess
from amaranth.back import rtlil
import re


def get_size(module, *args, **kwargs):
    rtlil_text = rtlil.convert(module, *args, **kwargs)

    script = """
        read_ilang <<rtlil
        {}
        rtlil

        synth -flatten -noabc
        read_liberty -lib /Users/anuejn/tmp/openlane-ci-designs/inverter/runs/RUN_2023-08-04_11-58-02/tmp/5221c3280114471a8e38997698419cbb.lib
        abc -liberty /Users/anuejn/tmp/openlane-ci-designs/inverter/runs/RUN_2023-08-04_11-58-02/tmp/5221c3280114471a8e38997698419cbb.lib
        dfflibmap -liberty /Users/anuejn/tmp/openlane-ci-designs/inverter/runs/RUN_2023-08-04_11-58-02/tmp/5221c3280114471a8e38997698419cbb.lib
        opt -full
        stat -liberty /Users/anuejn/tmp/openlane-ci-designs/inverter/runs/RUN_2023-08-04_11-58-02/tmp/5221c3280114471a8e38997698419cbb.lib
    """.format(rtlil_text)

    popen = subprocess.Popen(["yosys", "-s", "-"],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding="utf-8")
    output, error = popen.communicate(script) 
    # print(output)   

    try:
        cells = float(re.search("Chip area for module '\\\\top':\\W*(\\d+)", output).group(1))
    except:
        cells = 0

    return cells

