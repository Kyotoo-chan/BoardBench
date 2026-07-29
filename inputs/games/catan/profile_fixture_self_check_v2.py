#!/usr/bin/env python3
"""Evaluator-neutral complete-payload reconstruction checks for CATAN profile v2."""
from __future__ import annotations
import copy,importlib.util,json
from pathlib import Path
MODULE_PATH=Path(__file__).with_name('implementation.py');PROFILE_PATH=Path(__file__).with_name('GAME_PROFILE.json')
def load_module():
 spec=importlib.util.spec_from_file_location('fixture_checked_implementation',MODULE_PATH);assert spec and spec.loader;module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def roundtrip(game,payload,label):
 rebuilt=game.state_from_data(copy.deepcopy(payload));assert game.state_to_data(rebuilt)==payload,f'{label} did not round-trip';game.current_player(rebuilt);game.is_terminal(rebuilt);game.returns(rebuilt)
 for action in game.legal_actions(rebuilt):
  encoded=game.action_to_data(action);assert game.action_to_data(game.action_from_data(copy.deepcopy(encoded)))==encoded
 for player in range(payload['data']['configuration']['players']):game.observation_to_data(rebuilt,player)
def zero():return {'wood':0,'brick':0,'wool':0,'grain':0,'ore':0}
def frames():return [
 {'type':'discard','required':{'1':2},'selected':{'1':{'wood':1,'brick':1,'wool':0,'grain':0,'ore':0}},'submitted_players':[],'resume_phase':'robber_move','resume_current_player':0},
 {'type':'robber_move','resume_phase':'trade','resume_current_player':0,'source':'seven'},
 {'type':'robber_steal','resume_phase':'trade','resume_current_player':0,'victims':[1],'source':'seven'},
 {'type':'trade_offer','partner':1,'give':{'wood':1,'brick':0,'wool':0,'grain':0,'ore':0},'take':{'wood':0,'brick':1,'wool':0,'grain':0,'ore':0},'status':'awaiting_response','resume_phase':'trade','resume_current_player':0},
 {'type':'road_building','resume_phase':'build','resume_current_player':0,'remaining':2}]
def main():
 module=load_module();profile=json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
 for players in profile['player_counts']['supported']:
  game=module.Game(num_players=players,seed=1);base=game.state_to_data(game.initial_state());assert base['schema']==profile['state_schema'];assert set(base['data'])==set(profile['state_data']['required']);assert len(base['data']['players'])==players;roundtrip(game,base,f'initial {players}p')
  for frame in frames():
   payload=copy.deepcopy(base);payload['data']['pending']=[frame];payload['data']['phase']=frame['type'] if frame['type']!='trade_offer' else 'trade_offer';payload['data']['current_player']=1 if frame['type'] in {'discard','trade_offer'} else 0;roundtrip(game,payload,f"{players}p {frame['type']}")
  payload=copy.deepcopy(base);knight_move={'type':'robber_move','resume_phase':'discard','resume_current_player':1,'source':'knight'};payload['data']['phase']='robber_move';payload['data']['pending']=[frames()[0],knight_move];payload['data']['turn']['development_played']=True;roundtrip(game,payload,f'{players}p nested interrupt')
  payload=copy.deepcopy(base);payload['data']['chance']['scripted_rolls']=[[3,4],[6,6]];payload['data']['chance']['scripted_steals']=['wood','ore'];roundtrip(game,payload,f'{players}p scripted chance')
  payload=copy.deepcopy(base);payload['data']['phase']='terminal';payload['data']['terminal']=True;payload['data']['winner']=0;payload['data']['pending']=[];roundtrip(game,payload,f'{players}p terminal')
 for players in profile['player_counts']['unsupported']:
  try:module.Game(num_players=players,seed=1)
  except ValueError:pass
  else:raise AssertionError(f'unsupported player count accepted: {players}')
 print('catan-v2-profile-fixture-self-check OK')
if __name__=='__main__':main()
