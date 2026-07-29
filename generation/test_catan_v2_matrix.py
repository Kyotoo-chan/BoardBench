import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'inputs/games/catan'

def load(name):return json.loads((GAME/name).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

class CatanV2MatrixTests(unittest.TestCase):
 def test_assigned_sources_and_fresh_render_manifests(self):
  expected={'game_rules.pdf':'e0673fa93040f5b43908b215f52573878f586d26827d3a4f07c2ef8f8a947cf3','game_almanac.pdf':'8fe89cc65308c08104a2b2afd2f8edae24e8c608383420b044a6f35cd2c611bc'}
  for name,digest in expected.items():self.assertEqual(sha(GAME/name),digest)
  for name,pages in [('game_rules_render_manifest_v2.json',4),('game_almanac_render_manifest_v2.json',24)]:
   m=load(name);self.assertEqual(m['dpi'],150);self.assertEqual(len(m['pages']),pages);self.assertTrue(m['renderer']);self.assertTrue(m['renderer_version']);self.assertTrue(all(len(x['sha256'])==64 for x in m['pages']))
 def test_atomic_inventory_and_decisions(self):
  claims=load('claims_v2.json')['claims'];by={x['id']:x for x in claims}
  self.assertEqual(len(by),len(claims));self.assertEqual(Counter(x['classification'] for x in claims),{'clear':104,'missing':17,'ambiguous':2,'conflicting':1,'untestable':1})
  for claim in claims:
   self.assertIn(claim['classification'],{'clear','ambiguous','missing','conflicting','untestable'});self.assertIsInstance(claim['material'],bool);self.assertIsInstance(claim['testable'],bool);self.assertGreater(claim['source']['page'],0);self.assertTrue(claim['source']['quote']);self.assertIn(claim['source']['source_id'],{'CATAN22-RULES','CATAN22-ALMANAC'})
  decisions=load('decisions_v2.json')['decisions'];covered={i for d in decisions for i in d['claim_ids']}
  required={x['id'] for x in claims if x['material'] and x['testable'] and x['classification']!='clear'}
  self.assertEqual(covered,required);self.assertTrue(all(d['status']=='approved' for d in decisions))
 def test_complete_proposed_matrix(self):
  claims={x['id']:x for x in load('claims_v2.json')['claims']};m=load('scenario_matrix_v2.json');self.assertEqual(m['status'],'frozen-for-v2-intervention-comparison-r3');self.assertIn('3 and 4 players',m['scope']);self.assertEqual(len(m['scenarios']),55);self.assertEqual(sum(x['basis']=='clear' for x in m['scenarios']),40);self.assertEqual(sum(x['basis']=='human_decision' for x in m['scenarios']),15)
  mapped=set();human_mapped=set()
  for s in m['scenarios']:
   self.assertTrue(s['fact_ids']);self.assertTrue(s['expectation'])
   for fid in s['fact_ids']:
    self.assertIn(fid,claims)
    if s['basis']=='clear':self.assertEqual(claims[fid]['classification'],'clear',s['id']);mapped.add(fid)
    else:self.assertNotEqual(claims[fid]['classification'],'clear',s['id']);human_mapped.add(fid)
  required={i for i,c in claims.items() if c['classification']=='clear' and c['material'] and c['testable']};human_required={i for i,c in claims.items() if c['classification']!='clear' and c['material'] and c['testable']}
  self.assertEqual(mapped,required);self.assertEqual(human_mapped,human_required);self.assertEqual(m['clear_required'],len(required));self.assertEqual(m['coverage_exceptions'],[])
 def test_player_counts_and_high_risk_cases_are_explicit(self):
  by={x['id']:x for x in load('scenario_matrix_v2.json')['scenarios']}
  for sid in ('CAT-R01A-3p-board-pieces','CAT-R01B-3p-starting-resources','CAT-R01C-3p-bank-deck-start','CAT-R02A-4p-board-pieces','CAT-R02B-4p-starting-resources','CAT-R02C-4p-bank-deck-start','CAT-R04A-board-inventory','CAT-R04B-resource-inventory','CAT-R04C-development-inventory','CAT-R04D-player-and-other-inventory','CAT-R03-player-range','CAT-R11-bilateral-consent','CAT-R20-longest-transfer-ties','CAT-R21-longest-cycles','CAT-R22-seven-discard','CAT-R26-private-simultaneous-discards','CAT-R34-active-immediate-win','CAT-R38-source-privacy','CAT-R40-shortage-package','CAT-R41-designated-oldest-start','CAT-R42-development-boundaries','CAT-R43-victory-during-card-effect','CAT-R44-finite-trade-bound','CAT-R45-discard-escrow-interrupt','CAT-R46-knight-robbery-required','CAT-R47-maritime-receive-differs'):self.assertIn(sid,by)
  self.assertIn('reject 2 and 5',by['CAT-R03-player-range']['expectation']);self.assertEqual(by['CAT-R41-designated-oldest-start']['fact_ids'],['CAT-M-OLDEST-INPUT'])
  self.assertNotIn('empty',by['CAT-R23-robber-move-steal']['expectation'].lower());self.assertNotIn('irrespective',by['CAT-R23-robber-move-steal']['expectation'].lower());self.assertIn('empty',by['CAT-R25-random-theft-no-victim']['expectation'].lower())
  self.assertIn('never by enumerating bundle subsets',by['CAT-R11-bilateral-consent']['expectation'])
  self.assertEqual([s for s in by if s.startswith('CAT-R4')],['CAT-R40-shortage-package','CAT-R41-designated-oldest-start','CAT-R42-development-boundaries','CAT-R43-victory-during-card-effect','CAT-R44-finite-trade-bound','CAT-R45-discard-escrow-interrupt','CAT-R46-knight-robbery-required','CAT-R47-maritime-receive-differs'])
  for sid,needle in [('CAT-R01B-3p-starting-resources','blue B has wood 1'),('CAT-R01C-3p-bank-deck-start','wood 17'),('CAT-R02B-4p-starting-resources','Red A has wood 2'),('CAT-R02C-4p-bank-deck-start','wood 15'),('CAT-R04A-board-inventory','wood 4'),('CAT-R04B-resource-inventory','19 each'),('CAT-R04C-development-inventory','14 Knights'),('CAT-R04D-player-and-other-inventory','15 roads')]:self.assertIn(needle,by[sid]['expectation'])
  matrix=load('scenario_matrix_v2.json');rows=[f"| `{s['id']}` | {s['basis']} | {', '.join(f'`{i}`' for i in s['fact_ids'])} | {s['expectation']} |" for s in matrix['scenarios']]
  expected='\n'.join(['# CATAN V2 approval matrix','',f"- status: **{matrix['status']}**",f"- scope: {matrix['scope']}",f"- claims: {matrix['claims_total']} total; {matrix['clear_required']} required clear",f"- scenarios: {len(matrix['scenarios'])} ({sum(s['basis']=='clear' for s in matrix['scenarios'])} clear, {sum(s['basis']=='human_decision' for s in matrix['scenarios'])} human decision)",'','| ID | Basis | Facts | Expectation |','|---|---|---|---|',*rows,'','## Numbering','','Numeric stems now extend through `R47`. The explicit setup/inventory splits `R01A`–`R01C`, `R02A`–`R02C`, and `R04A`–`R04D` produce 55 physical scenarios without renumbering prior stable IDs; `R40`–`R47` are intentionally contiguous.','','## Approval boundary','','No implementation or scoring starts until this complete matrix is approved. Claim mapping is not assertion completeness; each executable scenario will retain direct source evidence for every mapped fact.',''])
  self.assertEqual((GAME/'scenario_matrix_v2.md').read_text(encoding='utf-8'),expected)

if __name__=='__main__':unittest.main()
