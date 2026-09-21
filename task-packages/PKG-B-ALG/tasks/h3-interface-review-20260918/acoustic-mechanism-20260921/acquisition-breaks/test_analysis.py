import unittest
from analyze import analyze

def row(i,count,gate=True,valid=True,reason='acquiring'):
 return dict(capture='fixture',start=i*512,gate=gate,new_valid=valid,tracker=dict(fresh_valid=False,state='ACQUIRE' if count else 'SEARCH',acquire_count=count,reason=reason))
class Controls(unittest.TestCase):
 def test_restart_and_end(self):
  a=analyze([row(0,1),row(1,2),row(2,1)],'joint');self.assertEqual(a['break_counts'],{'spread_restart':1,'recording_end_censored':1});self.assertEqual(a['longest_eligible_run'],3)
 def test_gate_precedence(self):
  a=analyze([row(0,1),row(1,0,False,False,'baseline_rejected')],'joint');self.assertEqual(a['break_counts'],{'activity_gate_closed':1})
 def test_cone_and_geometry(self):
  a=analyze([row(0,1),row(1,0,True,True,'outside_cone'),row(2,1),row(3,0,True,False,'baseline_rejected')],'joint');self.assertEqual(a['break_counts'],{'outside_cone':1,'geometry_rejected':1})
if __name__=='__main__':unittest.main()
