import subprocess
from nmigen.back import rtlil
import re


def get_size(module, *args, **kwargs):
    rtlil_text = rtlil.convert(module, *args, **kwargs)

    script = """
        read_ilang <<rtlil
        {}
        rtlil
        flatten
        
        synth_ecp5 -abc9
    """.format(rtlil_text)

    popen = subprocess.Popen(["yosys", "-s", "-"],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             encoding="utf-8")
    output, error = popen.communicate(script)

    print(output)

    try:
        cells = int(re.search("LUT4\\W*(\\d+)", output).group(1))
    except:
        cells = 0

    return cells

