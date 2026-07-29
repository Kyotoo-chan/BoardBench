import hashlib,importlib.util,json,py_compile,shutil,unittest
from pathlib import Path
from generation.run_hardened import build_workspace,load_config
from generation.source_condition import validate_pair
from checks.run_scenarios_v4 import load_suite
ROOT=Path(__file__).resolve().parents[1];GAME=ROOT/'inputs/games/catan';CONFIG=GAME/'run_v2_original.json';SUITE=ROOT/'checks/scenarios/catan_v2.json';MATRIX=GAME/'scenario_matrix_v2.json'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
class CatanV2PacketTests(unittest.TestCase):
 def test_profile_freezes_3p_4p_and_finite_actions(self):
  p=load(GAME/'environment_profile_v2.json');self.assertEqual((p['state_schema'],p['action_schema'],p['observation_schema']),('boardbench/catan/state/2','boardbench/catan/action/2','boardbench/catan/observation/2'));self.assertEqual(p['player_counts'],{'supported':[3,4],'unsupported':[2,5]});self.assertEqual(p['configuration']['oldest_player'],0)
  self.assertEqual(p['setup_by_player_count']['3']['colors'],['blue','orange','white']);self.assertEqual(p['setup_by_player_count']['4']['colors'],['red','blue','orange','white']);self.assertEqual(p['setup_by_player_count']['3']['starting_bank'],{'wood':17,'brick':18,'wool':18,'grain':17,'ore':16});self.assertEqual(p['setup_by_player_count']['4']['starting_bank'],{'wood':15,'brick':18,'wool':18,'grain':16,'ore':16})
  types=p['action_data']['types'];self.assertEqual(types['begin_domestic_trade'],{'partner':'int'});self.assertEqual(types['add_trade_item'],{'direction':'give|take','resource':'resource_id'});self.assertNotIn('bundle',json.dumps(types));self.assertTrue({'propose_domestic_trade','accept_domestic_trade','reject_domestic_trade'} <= set(types));self.assertIn('bottom-to-top',p['state_data']['pending']['type']);self.assertIn('one-development-card-per-turn',p['representation_choices']['pending_stack']);self.assertIn('excludes every unrevealed',p['observation_data']['visible_scores'][0])
 def test_suite_exactly_matches_approved_matrix_and_claims(self):
  suite=load_suite(SUITE,ROOT);matrix=load(MATRIX);claims={c['id']:c for c in load(GAME/'claims_v2.json')['claims']};self.assertEqual(len(suite['scenarios']),55);self.assertEqual(len(suite['claim_coverage']['required']),99);self.assertEqual(suite['claim_coverage']['mapping_coverage'],1.0);self.assertEqual(suite['coverage_exceptions'],[])
  self.assertEqual([(s['id'],s['basis'],s['fact_ids'],s['title'],s['expectation']) for s in suite['scenarios']],[(s['id'],s['basis'],s['fact_ids'],s['title'],s['expectation']) for s in matrix['scenarios']]);self.assertEqual(sum(len(s['cases']) for s in suite['scenarios']),113)
  for scenario in suite['scenarios']:
   expected=[{'fact_id':fid,**claims[fid]['source']} for fid in scenario['fact_ids']];self.assertEqual(scenario['supporting_sources'],expected,scenario['id']);self.assertEqual(scenario['source'],claims[scenario['fact_ids'][0]]['source']);self.assertTrue(scenario['cases'])
 def test_every_case_uses_frozen_action_vocabulary(self):
  suite=load(SUITE);profile=load(GAME/'environment_profile_v2.json');types=profile['action_data']['types']
  def check_selector(selector,label):
   if not selector:return
   action=selector.get('adapter')
   if action is None:return
   self.assertIn(action['type'],types,label);self.assertEqual(set(action.get('args',{})),set(types[action['type']]),label)
  for scenario in suite['scenarios']:
   for case in scenario['cases']:
    label=f"{scenario['id']}:{case.get('name')}"
    for step in case.get('steps',[]):check_selector(step.get('action',{}),label)
    expected=[case.get('initial',{}),case.get('expect',{})]+[step.get('expect',{}) for step in case.get('steps',[])]
    for item in expected:
     adapter=item.get('adapter',{}) if isinstance(item,dict) else {}
     for probe in adapter.get('action_legal',[]):check_selector({'adapter':probe['selector']},label)
     for action_type in adapter.get('legal_action_type_not',[])+adapter.get('legal_action_type_any',[]):self.assertIn(action_type,types,label)
 def test_adapter_is_contract_v2_and_historical_files_unchanged(self):
  path=ROOT/'checks/scenario_adapters/catan_v2.py';py_compile.compile(str(path),doraise=True);text=path.read_text(encoding='utf-8');self.assertIn('boardbench/catan/state/2',text);self.assertIn('"accept_domestic_trade"',text);self.assertIn('data["pending"][-1]',text);self.assertNotIn('public_scores',text)
  self.assertEqual(sha(ROOT/'checks/scenario_adapters/catan.py'),'fce085d7dd545793603260f85dd8157d63674ac4fe8c4a70e0f400253de83454');self.assertEqual(sha(ROOT/'checks/scenarios/catan.json'),'b7a4f653376d18d3d1ad1dd12aff596b0308946ee69602cf613c409848d26cfe')
 def test_frozen_manifest_hashes_match(self):
  manifest=load(GAME/'experiment_manifest_v2.json');self.assertEqual(manifest['status'],'frozen-pre-generation');self.assertEqual(manifest['evaluation']['status'],'not_run');self.assertEqual((manifest['evaluation']['scenarios'],manifest['evaluation']['named_cases'],manifest['evaluation']['required_clear_claims']),(51,107,99))
  for item in manifest['condition']['sources']:
   self.assertEqual(sha(ROOT/item['path']),item['sha256'],item['source_id'])
  revision2=load(GAME/'evaluator_revision_v2_r2.json');self.assertEqual(revision2['prior_frozen_manifest']['sha256'],sha(GAME/'experiment_manifest_v2.json'))
  revision3=load(GAME/'evaluator_revision_v2_r3.json');self.assertEqual(revision3['prior_revision']['sha256'],sha(GAME/'evaluator_revision_v2_r2.json'));self.assertEqual(revision3['rubric_version'],'catan-2022-v2-atomic-r3-2026-07-29');self.assertEqual(revision3['evaluation'],{'scenarios':55,'named_cases':113,'clear_basis':40,'human_decision_basis':15,'required_clear_claims':99})
  for name,item in revision3['artifacts'].items():self.assertEqual(sha(ROOT/item['path']),item['sha256'],name)
 def test_interventions_are_independent_and_evaluator_blind(self):
  original=load_config(CONFIG);configs=[load_config(GAME/'run_v2_clear_rule_emphasis.json'),load_config(GAME/'run_v2_clarified.json')]
  for config in configs:
   validate_pair(original['sources'],config['sources'],GAME,GAME)
   for key in ('profile','agentic_self_check','profile_fixture_self_check','prompt','contract','model','effort','verbosity','max_repairs','timeout','output_stem'):self.assertEqual(config[key],original[key],key)
   supplement=(GAME/config['sources'][-1]['path']).read_text(encoding='utf-8').lower()
   for hidden in ('cat-r18','original_scenarios','judge','score:','claims_v2'):self.assertNotIn(hidden,supplement)
  self.assertEqual(configs[0]['intervention_kind'],'clear_rule_emphasis');self.assertEqual(configs[1]['intervention_kind'],'source_gap_clarification');self.assertNotEqual(configs[0]['sources'][-1]['sha256'],configs[1]['sources'][-1]['sha256'])
 def test_original_packet_exact_allowlist(self):
  config=load_config(CONFIG);workspace,images,allowed,_immutable,renders=build_workspace(config)
  try:
   self.assertEqual(len(images),28);self.assertEqual(set(renders),{'game_rules_pages/render_manifest.json','game_almanac_pages/render_manifest.json'});self.assertEqual({s['role'] for s in config['sources']},{'publisher_rulebook','publisher_companion'})
   for present in ('game_rules.pdf','game_almanac.pdf','GAME_PROFILE.json','agentic_self_check.py','profile_fixture_self_check.py','TASK.txt','SOURCE_MANIFEST.json'):self.assertIn(present,allowed)
   for hidden in ('claims_v2.json','decisions_v2.json','scenario_matrix_v2.json','catan_v2.json'):self.assertNotIn(hidden,allowed)
  finally:shutil.rmtree(workspace,ignore_errors=True)
 def test_packet_files_compile(self):
  py_compile.compile(str(GAME/'profile_fixture_self_check_v2.py'),doraise=True);py_compile.compile(str(ROOT/'checks/scenario_adapters/catan_v2.py'),doraise=True)
if __name__=='__main__':unittest.main()
