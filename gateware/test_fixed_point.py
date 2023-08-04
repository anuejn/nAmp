import math
import unittest
from itertools import product

from amaranth import *
from amaranth.sim import Simulator

from fixed_point import *


class TestFixedPoint(unittest.TestCase):
    fmt = Q(8, 16)
    test_values = [math.pi, math.e, math.sqrt(2), -.5, -42]

    def _resolve(self, expr):
        sim = Simulator(Module())

        a = []

        def testbench():
            a.append((yield expr))

        sim.add_process(testbench)
        sim.run()
        return a[0]

    def _resolve_fp(self, expr: FixedPointValue):
        return expr.fmt.to_float(self._resolve(expr.value))

    def test_conversion(self):
        for f in self.test_values:
            i = self.fmt.to_int(f)
            roundtripped = self.fmt.to_float(i)
            self.assertLess(abs(roundtripped - f), 0.001, "real: {}; got: {}; int: {}".format(f, roundtripped, i))

    def test_const_math(self):
        for a, b in product(self.test_values, self.test_values):
            real = a * b
            fp = self._resolve_fp(self.fmt.Const(a) * self.fmt.Const(b))
            self.assertLess(abs(real - fp), 0.001, "real: {}; got: {}".format(real, fp))

        for a, b in product(self.test_values, self.test_values):
            real = a + b
            fp = self._resolve_fp(self.fmt.Const(a) + self.fmt.Const(b))
            self.assertLess(abs(real - fp), 0.001, "real: {}; got: {}".format(real, fp))

        for a, b in product(self.test_values, self.test_values):
            real = a - b
            fp = self._resolve_fp(self.fmt.Const(a) - self.fmt.Const(b))
            self.assertLess(abs(real - fp), 0.001, "real: {}; got: {}".format(real, fp))

    def test_cast(self):
        for v in self.test_values:
            fp = self._resolve_fp(self.fmt.Const(v).cast(Q(10, 32)))
            self.assertLess(abs(v - fp), 0.001, "real: {}; got: {}".format(v, fp))

        for v in self.test_values:
            fp = self._resolve_fp(self.fmt.Const(v).cast(Q(10, 3), allow_precision_loss=True))
            self.assertLess(abs(v - fp), 0.1, "real: {}; got: {}".format(v, fp))

        for v in self.test_values:
            fp = self._resolve_fp(self.fmt.Const(v).cast(Q(10, 0), allow_precision_loss=True))
            self.assertLess(abs(v - fp), 1, "real: {}; got: {}".format(v, fp))

        for v in self.test_values:
            fp = self._resolve_fp(self.fmt.Const(v).cast(Q(1, 16), allow_clamp=True))
            if abs(v) > 1:
                self.assertLess(abs(fp) - 1, 1e-10, "real: {}; got: {}".format(v, fp))
            else:
                self.assertLess(abs(v - fp), 1e-10, "real: {}; got: {}".format(v, fp))

    def test_const_clamp(self):
        self.assertEqual(self.fmt.to_float(self.fmt.max), self._resolve_fp(self.fmt.Const(20000, allow_clamp=True)))
        self.assertEqual(self.fmt.to_float(self.fmt.min), self._resolve_fp(self.fmt.Const(-20000, allow_clamp=True)))

    def test_min_max(self):
        print(self.fmt.to_float(self.fmt.min))
        print(self.fmt.to_float(self.fmt.max))
