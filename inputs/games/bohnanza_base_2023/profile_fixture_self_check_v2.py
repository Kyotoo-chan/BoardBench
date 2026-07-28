#!/usr/bin/env python3
"""Evaluator-neutral canonical fixture reconstruction check for Bohnanza Base 2023 V2."""
from __future__ import annotations
import copy, importlib.util, json
from collections import Counter
from pathlib import Path

MODULE_PATH=Path(__file__).with_name("implementation.py")
PROFILE_PATH=Path(__file__).with_name("GAME_PROFILE.json")
COUNTS={"gartenbohne":6,"rote_bohne":8,"augenbohne":10,"sojabohne":12,"brechbohne":14,"saubohne":16,"feuerbohne":18,"blaue_bohne":20}

def load_module():
 spec=importlib.util.spec_from_file_location("fixture_checked_implementation",MODULE_PATH)
 if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {MODULE_PATH}")
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def cards(data):
 out=[]
 for player in data["players"]:
  out.extend(player["hand"])
  for field in player["fields"]: out.extend(field)
 for name in ("deck","discard","revealed","reserve"): out.extend(data["zones"][name])
 for group in data["zones"]["pending_received"]: out.extend(group)
 return out

def card_total(data): return len(cards(data))+sum(player["coins"] for player in data["players"])

def roundtrip(game,payload,label):
 rebuilt=game.state_from_data(copy.deepcopy(payload));actual=game.state_to_data(rebuilt)
 assert actual==payload,f"{label} did not round-trip"
 game.current_player(rebuilt);game.is_terminal(rebuilt);game.returns(rebuilt)
 for action in game.legal_actions(rebuilt):
  encoded=game.action_to_data(action)
  assert game.action_to_data(game.action_from_data(copy.deepcopy(encoded)))==encoded
 for player in range(payload["data"]["configuration"]["players"]):
  obs=game.observation_to_data(rebuilt,player)
  assert obs["schema"]=="boardbench/bohnanza-base-2023/observation/2"

def blank(base,phase):
 payload=copy.deepcopy(base);data=payload["data"];inventory=Counter(cards(data))
 for player in data["players"]: player["hand"]=[];player["fields"]=[[] for _ in player["fields"]];player["coins"]=0
 data["zones"]={"deck":[],"discard":[],"revealed":[],"pending_received":[[] for _ in data["players"]],"reserve":sorted(inventory.elements())}
 data["current_player"]=data["active_player"]=data["start_player"]=0;data["phase"]=phase;data["depletions"]=0;data["pending"]=None;data["terminal"]=phase=="terminal";data["winner"]=0 if phase=="terminal" else None;data["turn_number"]=0;data["chance"]["counter"]=0
 return payload

def move(data,target,card): data["zones"]["reserve"].remove(card);target.append(card)

def main():
 module=load_module();profile=json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
 for count in profile["player_counts"]["supported"]:
  game=module.Game(num_players=count,seed=20260727);payload=game.state_to_data(game.initial_state())
  assert payload["schema"]==profile["state_schema"]
  assert Counter(cards(payload["data"]))==Counter(COUNTS)
  assert len(payload["data"]["players"])==count
  roundtrip(game,payload,f"{count}-player initial")
 for count in profile["player_counts"]["unsupported"]:
  try: module.Game(num_players=count,seed=1)
  except ValueError: pass
  else: raise AssertionError(f"unsupported count accepted: {count}")
 game=module.Game(num_players=3,seed=20260727);base=game.state_to_data(game.initial_state())
 fixtures=[]
 trade=blank(base,"trade_response");d=trade["data"];move(d,d["players"][0]["hand"],"blaue_bohne");move(d,d["players"][1]["hand"],"feuerbohne");d["current_player"]=1;d["pending"]={"type":"trade","actor":0,"partner":1,"offered":[{"owner":0,"zone":"hand","index":0,"bean":"blaue_bohne"}],"requested":[{"owner":1,"zone":"hand","index":0,"bean":"feuerbohne"}],"awaiting_player":1};fixtures.append(("trade_response",trade))
 phase3=blank(base,"plant_received");d=phase3["data"];move(d,d["zones"]["pending_received"][0],"sojabohne");move(d,d["zones"]["pending_received"][1],"rote_bohne");move(d,d["zones"]["revealed"],"gartenbohne");fixtures.append(("multi-owner phase3",phase3))
 recycle=blank(base,"reveal");d=recycle["data"];move(d,d["zones"]["deck"],"blaue_bohne");move(d,d["zones"]["discard"],"feuerbohne");move(d,d["zones"]["discard"],"sojabohne");d["depletions"]=1;fixtures.append(("recycle",recycle))
 privacy=blank(base,"plant_first");d=privacy["data"];move(d,d["players"][0]["hand"],"blaue_bohne");move(d,d["players"][1]["hand"],"feuerbohne");move(d,d["players"][1]["hand"],"sojabohne");fixtures.append(("privacy",privacy))
 coin=blank(base,"trade");d=coin["data"];d["zones"]["reserve"].remove("rote_bohne");d["players"][0]["coins"]=1;fixtures.append(("coin inventory",coin))
 terminal=blank(base,"terminal");fixtures.append(("terminal",terminal))
 for label,payload in fixtures:
  assert card_total(payload["data"])==sum(COUNTS.values());roundtrip(game,payload,label)
 obs=game.observation_to_data(game.state_from_data(privacy),0)["data"];opponent=next(x for x in obs["opponents"] if x["id"]==1)
 assert opponent=={"id":1,"hand_size":2,"front_card":"feuerbohne"}
 assert "sojabohne" not in repr(opponent) and "deck" not in obs
 print("profile-fixture-self-check OK")
if __name__=="__main__": main()
