from sqlmodel import Session,select
from model import models
from datetime import timezone,datetime

def get_conversation_history(user_id,session: Session):
    statement=select(models.ConversationHistory).where(models.ConversationHistory.user_id==user_id)
    conversation_history=session.exec(statement).first()
    if conversation_history is not None:
        return conversation_history.messages
    else:
        return None

def update_conversation_history(user_id,role,message,continuity,session:Session):
     statement=select(models.ConversationHistory).where(models.ConversationHistory.user_id==user_id)
     conversation_history=session.exec(statement).first()
     snippet={
               "role":role,
               "text":message,
               "continuity":continuity,
               "timestamp": datetime.now(timezone.utc).isoformat()
          }
     if conversation_history is not None:
          conversations=conversation_history.messages
          conversations.append(snippet)
          conversation_history.messages=conversations
          session.add(conversation_history)
          session.commit()
     else:
          record=models.ConversationHistory(user_id=user_id,messages=[snippet])
          session.add(record)
          session.commit()

def reset_conversation(user_id,session):
    statement=select(models.ConversationHistory).where(models.ConversationHistory.user_id==user_id)
    conversation_history=session.exec(statement).first()
    conversation_history.messages=[]
    session.add(conversation_history)
    session.commit()





