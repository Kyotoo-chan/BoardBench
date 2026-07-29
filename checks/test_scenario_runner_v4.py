from types import SimpleNamespace
import unittest
from checks.run_scenarios_v4 import run_scenario_v4
class DummyGame:
 def legal_actions(self,state):return []
 def action_to_name(self,action):return str(action)
class ScenarioCasesV4Tests(unittest.TestCase):
 def test_cases_run_independently(self):
  seen=[];adapter=SimpleNamespace(setup=lambda module,game,fixture:{'value':fixture['value']},check=lambda module,game,state,expected:seen.append((state['value'],expected['value'])))
  run_scenario_v4(DummyGame(),{'source':{'page':1,'quote':'A sufficiently long source quotation.'},'cases':[{'name':'one','fixture':{'value':1},'initial':{'adapter':{'value':1}}},{'name':'two','fixture':{'value':2},'initial':{'adapter':{'value':2}}}]},None,adapter)
  self.assertEqual(seen,[(1,1),(2,2)])
 def test_all_case_failures_are_reported(self):
  seen=[]
  def check(module,game,state,expected):seen.append(state['value']);raise AssertionError(f"bad {state['value']}")
  adapter=SimpleNamespace(setup=lambda module,game,fixture:{'value':fixture['value']},check=check)
  with self.assertRaisesRegex(AssertionError,'case one: bad 1; case two: bad 2'):
   run_scenario_v4(DummyGame(),{'source':{'page':1,'quote':'A sufficiently long source quotation.'},'cases':[{'name':'one','fixture':{'value':1},'initial':{'adapter':{'value':1}}},{'name':'two','fixture':{'value':2},'initial':{'adapter':{'value':2}}}]},None,adapter)
  self.assertEqual(seen,[1,2])
if __name__=='__main__':unittest.main()
