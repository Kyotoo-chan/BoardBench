import importlib.util
import json
import py_compile
import shutil
import unittest
from pathlib import Path

from checks.run_scenarios_v4 import load_suite
from checks.scenario_adapters import bohnanza_base_2023_v2 as adapter
from generation.run_hardened import build_workspace, load_config
from generation.source_condition import validate_pair

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'inputs/games/bohnanza_base_2023'
CONFIG=GAME/'run_v2_original.json'
EMPHASIS_CONFIG=GAME/'run_v2_clear_rule_emphasis.json'
EMPHASIS_REPEAT_CONFIG=GAME/'run_v2_clear_rule_emphasis_2.json'
STRUCTURED_CONFIG=GAME/'run_v2_structured_clarification_1.json'
SUITE=ROOT/'checks/scenarios/bohnanza_base_2023_v2.json'
MATRIX=GAME/'scenario_matrix_v2.json'

class BohnanzaV2Tests(unittest.TestCase):
 def test_matrix_suite_claim_coverage_parity(self):
  suite=load_suite(SUITE,ROOT);matrix=json.loads(MATRIX.read_text(encoding='utf-8'));coverage=suite['claim_coverage']
  self.assertEqual(matrix['status'],'approved-for-v2-evaluation')
  self.assertEqual(suite['rubric_version'],'bohnanza-base-2023-v2-atomic-2026-07-28')
  self.assertEqual(len(suite['scenarios']),42)
  self.assertEqual(sum(x['basis']=='clear' for x in suite['scenarios']),38)
  self.assertEqual(sum(x['basis']=='human_decision' for x in suite['scenarios']),4)
  self.assertEqual(len(coverage['required']),81);self.assertEqual(coverage['mapping_coverage'],80/81)
  self.assertEqual(coverage['coverage_exceptions'],['BOHN-C-HARVEST-ANYTIME'])
  self.assertEqual(suite['coverage_exceptions'],['BOHN-C-HARVEST-ANYTIME'])
  self.assertEqual([(x['id'],x['basis'],x['fact_ids'],x['title'],x['expectation']) for x in matrix['scenarios']],[(x['id'],x['basis'],x['fact_ids'],x['title'],x['expectation']) for x in suite['scenarios']])
  py_compile.compile(str(ROOT/suite['adapter']),doraise=True)
 def test_human_cases_exactly_match_approved_decisions(self):
  decisions=json.loads((GAME/'decisions_v2.json').read_text())['decisions'];approved={c for x in decisions if x['status']=='approved' for c in x['claim_ids']}
  suite=json.loads(SUITE.read_text());human={c for x in suite['scenarios'] if x['basis']=='human_decision' for c in x['fact_ids']}
  self.assertEqual(human,approved)
 def test_profile_semantics(self):
  p=json.loads((GAME/'environment_profile_v2.json').read_text())
  self.assertEqual(p['player_counts'],{'supported':[3,4,5],'unsupported':[2,6]})
  self.assertEqual((p['state_schema'],p['action_schema'],p['observation_schema']),('boardbench/bohnanza-base-2023/state/2','boardbench/bohnanza-base-2023/action/2','boardbench/bohnanza-base-2023/observation/2'))
  self.assertIn('final item is next draw',p['state_data']['zones']['deck'][0])
  self.assertEqual(p['observation_data']['opponents'][0],{'id':'int','hand_size':'int','front_card':'bean_id|null'})
  self.assertIn('Any player',p['representation_choices']['phase3_order'])
  self.assertIn('atomically only on acceptance',p['representation_choices']['trade_refs'])
  self.assertIn('winner',p['state_data']['required'])
 def test_adapter_deck_fixture_is_bottom_to_top_and_chance_is_strict(self):
  class FakeGame:
   def initial_state(self):return {'schema':adapter.STATE_SCHEMA,'data':{'configuration':{'players':3,'seed':1,'variant':'base_2023'},'current_player':0,'active_player':0,'start_player':0,'phase':'plant_first','terminal':False,'winner':None,'players':[{'id':i,'hand':[],'fields':[[],[]],'coins':0} for i in range(3)],'zones':{'deck':['blaue_bohne','feuerbohne'],'discard':[],'revealed':[],'pending_received':[[],[],[]],'reserve':[]},'depletions':0,'pending':None,'turn_number':0,'chance':{'seed':1,'counter':0}}}
   def state_to_data(self,state):return state
   def state_from_data(self,payload):
    self_outer.assertEqual(set(payload['data']['chance']),{'seed','counter'})
    return payload
  self_outer=self
  class Module:
   @staticmethod
   def Game(num_players=3,seed=1):return FakeGame()
  state=adapter.setup(Module(),FakeGame(),{'seed':9,'deck':['blau','feuer'],'phase':'reveal'})
  self.assertEqual(state['data']['zones']['deck'],['feuerbohne','blaue_bohne'])
  coin_state=adapter.setup(Module(),FakeGame(),{'coins':{'0':1},'phase':'trade'})
  self.assertEqual(adapter._card_total(coin_state['data']),2)
  self.assertEqual(len(coin_state['data']['zones']['reserve']),1)

 def test_privacy_allows_deck_size_but_only_exact_public_keys(self):
  allowed=json.loads((GAME/'environment_profile_v2.json').read_text())['observation_data']['required']
  state={'schema':adapter.STATE_SCHEMA,'data':{'configuration':{'players':2,'seed':1,'variant':'base_2023'},'current_player':0,'active_player':0,'start_player':0,'phase':'trade','terminal':False,'winner':None,'players':[{'id':0,'hand':['blaue_bohne'],'fields':[[],[]],'coins':0},{'id':1,'hand':['feuerbohne','sojabohne'],'fields':[[],[]],'coins':0}],'zones':{'deck':['rote_bohne'],'discard':[],'revealed':[],'pending_received':[[],[]],'reserve':[]},'depletions':0,'pending':None,'turn_number':0,'chance':{'seed':1,'counter':0}}}
  observation={key:None for key in allowed};observation.update({'player':0,'current_player':0,'active_player':0,'start_player':0,'phase':'trade','terminal':False,'winner':None,'own_hand':['blaue_bohne'],'opponents':[{'id':1,'hand_size':2,'front_card':'feuerbohne'}],'fields':[[[],[]],[[],[]]],'coins':[0,0],'revealed':[],'deck_size':1,'discard_size':0,'pending_received_counts':[0,0],'pending':None,'turn_number':0})
  class Game:
   def state_to_data(self,value):return value
   def legal_actions(self,value):return []
   def observation_to_data(self,value,player):return {'schema':adapter.OBSERVATION_SCHEMA,'data':observation}
  adapter.check(None,Game(),state,{'private_hand_visibility':{'player':0,'own':['blau'],'opponents':{'1':['feuer','soja']},'allowed_keys':allowed}})
  observation['opponents'][0]['deep_cards']=['sojabohne']
  with self.assertRaises(AssertionError):adapter.check(None,Game(),state,{'private_hand_visibility':{'player':0,'own':['blau'],'opponents':{'1':['feuer','soja']},'allowed_keys':allowed}})

 def test_citations_and_non_tautological_boundaries_are_frozen(self):
  suite=json.loads(SUITE.read_text());claims={x['id']:x for x in json.loads((GAME/'claims_v2.json').read_text())['claims']};by={x['id']:x for x in suite['scenarios']}
  for scenario in suite['scenarios']:
   expected=[{'fact_id':fid,'source_id':claims[fid]['source']['source_id'],'page':claims[fid]['source']['page'],'quote':claims[fid]['source']['quote']} for fid in scenario['fact_ids']]
   self.assertEqual(scenario['supporting_sources'],expected,scenario['id'])
   self.assertEqual(len({x['fact_id'] for x in scenario['supporting_sources']}),len(scenario['fact_ids']))
  self.assertEqual(by['BOHN-R05-start-card-fixed']['steps'][0]['action']['adapter']['type'],'draw')
  self.assertGreaterEqual(len(by['BOHN-R06-seeded-start']['initial']['adapter']['seeded_start_probe']['seeds']),2)
  self.assertEqual(by['BOHN-R11-empty-hand-skip']['steps'][0]['action']['adapter']['type'],'pass')
  self.assertEqual(by['BOHN-R14-four-phase-turn']['steps'][-2]['settle'][0]['choose_contains_any'],['pass'])
  self.assertEqual(by['BOHN-R14-four-phase-turn']['steps'][-1]['action']['adapter']['type'],'draw')
  self.assertEqual([x['action']['adapter'].get('actor') for x in by['BOHN-R23-phase3-any-player-order']['steps'][:3]],[1,0,0])
  self.assertIn('draw',by['BOHN-R23-phase3-any-player-order']['steps'][1]['expect']['adapter']['legal_action_type_not'])
  for sid in ('BOHN-R38-first-recycle-reveal','BOHN-R39-second-recycle-draw'):self.assertEqual(by[sid]['fixture']['seed'],20260727)
  self.assertEqual(by['BOHN-R38-first-recycle-reveal']['steps'][0]['expect']['adapter']['revealed_prefix'],['blau'])
  self.assertEqual(by['BOHN-R39-second-recycle-draw']['steps'][0]['expect']['adapter']['hand_prefix']['0'],['garten','blau'])
  self.assertEqual(by['BOHN-R23-phase3-any-player-order']['steps'][2]['settle'][0]['choose_contains_any'],['pass'])
  self.assertEqual(by['BOHN-R23-phase3-any-player-order']['steps'][2]['expect']['adapter']['legal_action_type_any'],['draw'])
  self.assertEqual(by['BOHN-R40-third-depletion-phase2']['steps'][2]['action']['adapter']['args']['field'],1)
  self.assertEqual(by['BOHN-R40-third-depletion-phase2']['steps'][2]['settle'][0]['choose_contains_any'],['pass'])
  self.assertEqual(by['BOHN-R41-third-depletion-outside-phase2']['steps'][0]['action']['adapter']['type'],'draw');self.assertIn('field_sizes',by['BOHN-R41-third-depletion-outside-phase2']['steps'][0]['expect']['adapter'])
  self.assertFalse(by['BOHN-R42-final-score-tiebreak']['fixture'].get('terminal',False));self.assertNotIn('winner',by['BOHN-R42-final-score-tiebreak']['fixture']);self.assertEqual(by['BOHN-R42-final-score-tiebreak']['steps'][0]['action']['adapter']['type'],'draw')
  adapter_text=(ROOT/'checks/scenario_adapters/bohnanza_base_2023_v2.py').read_text()
  for hidden in ('second_plant_contract','field_type_contract','gift_outcomes','phase3_forced_harvest','harvest_conservation','stable_harvest_boundaries'):self.assertNotIn(hidden,adapter_text)
 def test_clear_rule_emphasis_is_separate_and_pair_identical(self):
  original=load_config(CONFIG)['sources'];emphasis_config=load_config(EMPHASIS_CONFIG)
  artifact=json.loads((GAME/'clear_rule_emphasis_v2.json').read_text())
  self.assertEqual(artifact['intervention_kind'],'clear_rule_emphasis')
  self.assertIn('not a source-gap clarification',artifact['authorship'])
  self.assertEqual({claim for item in artifact['emphasis'] for claim in item['claim_ids']},{'BOHN-C-TRADE-ANY-HAND-POSITION','BOHN-C-TRADE-UNEQUAL','BOHN-C-TRADE-CONSENT','BOHN-C-TRADE-TRANSFER-ON-ACCEPT','BOHN-C-PAYOUT-GARTEN','BOHN-C-PAYOUT-SOJA','BOHN-C-END-THIRD','BOHN-C-END-PHASE2-CONTINUE','BOHN-C-FINAL-HARVEST'})
  validate_pair(original,emphasis_config['sources'],GAME,GAME)
  repeat=load_config(EMPHASIS_REPEAT_CONFIG)
  for key in ('sources','profile','agentic_self_check','profile_fixture_self_check','prompt','contract','model','effort','verbosity','max_repairs','timeout','output_stem'):
   self.assertEqual(repeat[key],emphasis_config[key],key)
  self.assertEqual(repeat['adapted_from_run_id'],'v2_clear_rule_emphasis_1')
  workspace,_images,allowed,_immutable,_renders=build_workspace(emphasis_config)
  try:
   self.assertIn('clear_rule_emphasis_v2.json',allowed)
   for hidden in ('claims_v2.json','decisions_v2.json','rulefacts_v2.md','bohnanza_base_2023_v2.json'):self.assertNotIn(hidden,allowed)
  finally:shutil.rmtree(workspace,ignore_errors=True)
 def test_structured_clarification_is_balanced_and_evaluator_blind(self):
  original=load_config(CONFIG);config=load_config(STRUCTURED_CONFIG);guide=(GAME/'structured_clarification_v3.md').read_text(encoding='utf-8')
  validate_pair(original['sources'],config['sources'],GAME,GAME)
  self.assertNotIn('BOHN-C-',guide);self.assertNotIn('BOHN-R',guide)
  for term in ('Three-player games give every player three fields','any positive number of cards','all eight beanometers','harvest every field of every player','deeper opponent cards remain private'):
   self.assertIn(term,guide)
  for key in ('profile','agentic_self_check','profile_fixture_self_check','prompt','contract','model','effort','verbosity','max_repairs','timeout','output_stem'):
   self.assertEqual(config[key],load_config(EMPHASIS_REPEAT_CONFIG)[key],key)
  workspace,_images,allowed,_immutable,_renders=build_workspace(config)
  try:
   self.assertIn('STRUCTURED_CLARIFICATION.md',allowed)
   for hidden in ('claims_v2.json','decisions_v2.json','rulefacts_v2.md','bohnanza_base_2023_v2.json'):self.assertNotIn(hidden,allowed)
  finally:shutil.rmtree(workspace,ignore_errors=True)
 def test_original_packet_exact_allowlist(self):
  workspace,images,allowed,_immutable,renders=build_workspace(load_config(CONFIG))
  try:
   files={p.relative_to(workspace).as_posix() for p in workspace.rglob('*') if p.is_file()}
   self.assertEqual(files,allowed);self.assertEqual(len(images),2);self.assertEqual(set(renders),{'game_rules_pages/render_manifest.json'})
   for present in ('game_rules.pdf','GAME_PROFILE.json','agentic_self_check.py','profile_fixture_self_check.py','TASK.txt','SOURCE_MANIFEST.json'):self.assertIn(present,allowed)
   for hidden in ('claims_v2.json','decisions_v2.json','rulefacts_v2.md','scenario_matrix_v2.json','bohnanza_base_2023_v2.json'):self.assertNotIn(hidden,allowed)
  finally:shutil.rmtree(workspace,ignore_errors=True)
 def test_packet_files_compile(self):
  py_compile.compile(str(GAME/'profile_fixture_self_check_v2.py'),doraise=True);py_compile.compile(str(ROOT/'checks/scenario_adapters/bohnanza_base_2023_v2.py'),doraise=True)

if __name__=='__main__':unittest.main()
