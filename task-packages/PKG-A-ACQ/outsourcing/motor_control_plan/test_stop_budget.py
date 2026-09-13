"""Budget regression only (stdlib). Run: python test_stop_budget.py.
Outputs assertions summary; next inspect scope and safety table manually.
"""
import math, unittest
from size_dual_axis import stop_budget

class BudgetTests(unittest.TestCase):
    def test_retained_review_failure(self):
        r=stop_budget(.003,35,.37544,.8,.01)
        self.assertFalse(r['pass_budget'])
        self.assertAlmostEqual(r['travel_with_energy_and_tolerance_deg'],10.983614837439264,places=9)

    def test_continuous_interval_bound(self):
        for lo,hi,v,a,b in [(.01,.04,65,.14,.6),(.004,.012,35,.37544,.8)]:
            maximum=max(stop_budget(j,v,a,b,.01)['travel_with_energy_and_tolerance_deg'] for j in [lo,hi])
            self.assertLess(maximum,10)
            for i in range(1001):
                j=lo+(hi-lo)*i/1000
                # Independent expanded energy expression, radians.
                w=math.radians(v)
                ref=math.degrees((b*w*.03+j*w*w/2+b*a*.03**2/(2*j)+.01)/(b-a))+1.5
                actual=stop_budget(j,v,a,b,.01)['travel_with_energy_and_tolerance_deg']
                self.assertAlmostEqual(actual,ref,places=10)
                self.assertLessEqual(actual,maximum+1e-10)

    def test_piecewise_integration(self):
        # Independent midpoint integration of two constant-acceleration phases.
        for j in [.003,.004,.012]:
            v=math.radians(35);angle=0.;a=.37544;b=.8
            for duration,acc in [(.03,a/j)]:
                dt=duration/1000
                for _ in range(1000):angle+=(v+acc*dt/2)*dt;v+=acc*dt
            dt=(v/((b-a)/j))/1000
            for _ in range(1000):angle+=(v-(b-a)/j*dt/2)*dt;v-=(b-a)/j*dt
            total=math.degrees(angle+.01/(b-a))+1.5
            self.assertAlmostEqual(total,stop_budget(j,35,a,b,.01)['travel_with_energy_and_tolerance_deg'],places=9)

    def test_weak_brake_reason(self):
        r=stop_budget(.004,35,.37544,.2,.01)
        self.assertFalse(r['pass_budget'])
        self.assertEqual(r['reason'],'brake cannot overcome worst assisting torque')

    def test_invalid_numeric_inputs(self):
        for index in range(6):
            for bad in [float('nan'),float('inf'),-1]:
                args=[.004,35,.37544,.8,.01]
                if index==5:args[0]=0
                else:args[index]=bad
                with self.assertRaises(ValueError):stop_budget(*args)

if __name__=='__main__':unittest.main(verbosity=2)
