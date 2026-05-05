from model import models
from sqlmodel import Session,select
from datetime import datetime,timezone
from math import exp
import yaml
from pathlib import Path


def load_stimuli_tags(yaml_path=None):
    if yaml_path is None:
        yaml_path = Path(__file__).parent / "stimuli_tags.yaml" 
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    
    # Convert list of dicts into a usable dict
    return {
        item["tag"]: {
            "dopamine": item["dopamine_weight"],
            "survival": item["survival_weight"]
        }
        for item in data["stimuli_tags"]
    }


def compute_adjusted_dopamine(current, stimuli_tags, last_updated, now=None):
    now = now if now is not None else datetime.now(timezone.utc)
    if last_updated.tzinfo is None:
        last_updated = last_updated.replace(tzinfo=timezone.utc)
    minutes_passed = (now - last_updated).total_seconds() / 60
    decay_rate = 0.003
    alpha=0.3
    beta=0.5
    dopamine_delta=0
    defined_stimuli=load_stimuli_tags()
    for stimuli,score in stimuli_tags.items():
        dopamine_delta += score * defined_stimuli.get(stimuli, {}).get("dopamine", 0)
    decayed = current * exp(-decay_rate * minutes_passed)
    updated = decayed + dopamine_delta
    stablized=(1-alpha)*updated+alpha*decayed
    return max(0, min(1, stablized))

def compute_adjusted_survival(current, stimuli_tags, last_updated, now=None):
    now = now if now is not None else datetime.now(timezone.utc)
    if last_updated.tzinfo is None:
        last_updated = last_updated.replace(tzinfo=timezone.utc)
    minutes_passed = (now - last_updated).total_seconds() / 60
    decay_rate = 0.003
    alpha=0.3
    survival_delta=0
    defined_stimuli=load_stimuli_tags()
    for stimuli,score in stimuli_tags.items():
          print(stimuli)
          print(score)
          survival_delta += score * defined_stimuli.get(stimuli, {}).get("survival", 0)
          print(survival_delta)
    print(current)
    decayed = current * exp(-decay_rate * minutes_passed)
    print(survival_delta)
    print(decayed)
    updated = decayed + survival_delta
    stablized=(1-alpha)*updated+alpha*decayed
    return max(0, min(1, stablized))



def update_dopamine_and_survival_data(user_id,dopamine_user,survival_user,dopamine_ai,survival_ai,session: Session):
    statement = select(models.UserDopamineAndSurvival).where(models.UserDopamineAndSurvival.entity_id == user_id)
    current_metrics = session.exec(statement).first()
    if current_metrics is not None:
        current_metrics.dopamine_user = dopamine_user
        current_metrics.survival_user = survival_user
        current_metrics.survival_ai=survival_ai
        current_metrics.dopamine_ai=dopamine_ai
        current_metrics.timestamp = datetime.now(timezone.utc)
        session.add(current_metrics)
    else:
        current_metrics = models.UserDopamineAndSurvival(
            entity_id=user_id,
            dopamine_user=dopamine_user,
            survival_user=survival_user,
            dopamine_ai=dopamine_ai,
            survival_ai=survival_ai,
            timestamp=datetime.now(timezone.utc)
        )
        session.add(current_metrics)
    history_record = models.UserDopamineAndSurvivalHistory(
        entity_id=user_id,
     dopamine_user=dopamine_user,
            survival_user=survival_user,
            dopamine_ai=dopamine_ai,
            survival_ai=survival_ai,
        timestamp=datetime.now(timezone.utc)
    )
    session.add(history_record)
    session.commit()

def get_current_dopamine_and_survival(user_id: int, session: Session):
    statement=select(models.UserDopamineAndSurvival).where(models.UserDopamineAndSurvival.entity_id==user_id)
    metrics=session.exec(statement).first()
    if metrics is not None:
        return {
        "dopamine_user": metrics.dopamine_user,
        "survival_user": metrics.survival_user,
        "dopamine_ai": metrics.dopamine_ai,
        "survival_ai":metrics.survival_ai,
        "timestamp":metrics.timestamp
    }
    else:
        return None

def get_dopamine_and_survival_history(user_id: int,session:Session):
    statement=select(models.UserDopamineAndSurvivalHistory).where(models.UserDopamineAndSurvivalHistory.entity_id==user_id)
    historical_metrics=session.exec(statement).all()
    if historical_metrics is not None:
        return {
        "dopamine_user": [metrics.dopamine_user for metrics in historical_metrics],
        "survival_user": [metrics.survival_user for metrics in historical_metrics],
        "dopamine_ai": [metrics.dopamine_ai for metrics in historical_metrics],
        "survival_ai":[metrics.survival_ai for metrics in historical_metrics],
         "timestamps": [metrics.timestamp for metrics in historical_metrics]
    }
    else:
        return None

def reset_dopamine_survival_history(user_id,int,session:Session):
     statement=select(models.UserDopamineAndSurvivalHistory).where(models.UserDopamineAndSurvivalHistory.entity_id==user_id)
     historical_metrics=session.exec(statement).all()
     session.delete(historical_metrics)
     session.commit()

class EmotionalStateManager:
    def __init__(self,user_id,session):
        metrics=get_current_dopamine_and_survival(user_id,session)
        if metrics is None:
             self.initial_state={
            "dopamine_user":0.5,
            "survival_user":1.0,
            "dopamine_ai":0.5,
            "survival_ai":1.0
        } 
        else:
            self.initial_state={
        "dopamine_user": metrics["dopamine_user"],
        "survival_user": metrics["survival_user"],
        "dopamine_ai": metrics["dopamine_ai"],
        "survival_ai": metrics["survival_ai"]
            }
        self.user_id=user_id
        update_dopamine_and_survival_data(user_id,self.initial_state["dopamine_user"],self.initial_state["survival_user"],self.initial_state["dopamine_ai"],self.initial_state["survival_ai"],session)
    
    def recalculate_states(self,stimuli_user,stimuli_ai,session):
        current = get_current_dopamine_and_survival(self.user_id, session)
        if current is None:
            print("No existing dopamine/survival data — using defaults")
            current = {
            "dopamine_user": 0.5,
            "survival_user": 1.0,
            "dopamine_ai": 0.5,
            "survival_ai": 1.0,
            "timestamp": datetime.now(timezone.utc)
        }
        print("Calculating values")
        dopamine_user = compute_adjusted_dopamine(current["dopamine_user"], stimuli_user, current["timestamp"])
        print("Calculated dipamine")
        survival_user = compute_adjusted_survival(current["survival_user"], stimuli_user, current["timestamp"])
        print("Calculated dipamine")
        dopamine_ai = compute_adjusted_dopamine(current["dopamine_ai"], stimuli_ai, current["timestamp"])
        print("Calculated dipamine")
        survival_ai = compute_adjusted_survival(current["survival_ai"], stimuli_ai, current["timestamp"])
        print("Completed calc")
        update_dopamine_and_survival_data(
            self.user_id,
            dopamine_user,
            survival_user,
            dopamine_ai,
            survival_ai,
            session
        )

        self.initial_state = {
            "dopamine_user": dopamine_user,
            "survival_user": survival_user,
            "dopamine_ai": dopamine_ai,
            "survival_ai": survival_ai
        }

        return self.initial_state










    






        

    

        