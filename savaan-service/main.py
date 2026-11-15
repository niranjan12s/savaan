from fastapi import FastAPI, HTTPException, status, Depends,File,UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from auth import hash_password,create_access_token
from auth import pwd_context
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from middleware import request
from logger import logger
from model import models
from emotional_engine import generate_emotional_summary
from emotional_state import EmotionalStateManager
from episodic_memory import fetch_from_episodic_memory,parse_episodic_memory
from central_response_generator import generate_reply
from providers import factory

models.init_db()
llm = factory.get_llm()
vector_store = factory.get_vector_store()
state_store = factory.get_state_store()
transcriber = factory.get_transcriber()


app=FastAPI()
app.add_middleware(request.RequestIdMiddleWare)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

def get_session():
    with Session(models.engine) as session:
        yield session

@app.post("/register",status_code=status.HTTP_201_CREATED)
def register(user: models.User,session: Session=Depends(get_session)):
    existing_user=session.exec(select(models.UserEntity).where(models.UserEntity.email==user.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="User already exists, Please login to proceed")
    hashed_password=hash_password(user.password)
    new_user=models.UserEntity(email=user.email,hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/login")
def login(user: models.User, session: Session = Depends(get_session)):
    db_user = session.exec(
        select(models.UserEntity).where(models.UserEntity.email == user.email)
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    access_token=create_access_token(data={"userId":db_user.id})
    return {"access_token": access_token, "token_type": "bearer","userId":db_user.id}

@app.exception_handler(Exception)
async def all_exception_handler(request: request.Request,exc: Exception):
     logger.exception(f"Unhandled error on {request.url.path}")
     return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
@app.post("/users/{user_id}/respond")
async def respond(user_id: int,file: UploadFile = File(...)):
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    with open(file_path,"wb") as f:
        f.write(await file.read())
    try:
            transcript=transcriber.transcribe(file_path)
            logger.info(f"Transcription completed: {transcript}")
            stimuli_tag_data_user=generate_emotional_summary(transcript,llm)
            logger.info(f"tags: {stimuli_tag_data_user}")
            emotional_state=EmotionalStateManager(user_id,state_store)
            logger.info(f"Conversation_history: {state_store.get_conversation_history(user_id)}")
            episodic_results=fetch_from_episodic_memory(user_id,transcript,stimuli_tag_data_user,state_store,vector_store)
            logger.info(f"Episodic Results : {episodic_results}")
            main_reply=generate_reply(transcript,state_store.get_current_metrics(user_id),
                        state_store.get_metrics_history(user_id),
                        state_store.get_conversation_history(user_id),
                        episodic_results["documents"],llm)
            stimuli_tag_data_ai=generate_emotional_summary(main_reply["response"],llm)
            logger.info(f"tags: {stimuli_tag_data_ai}")
            history_now=state_store.get_conversation_history(user_id)
            if main_reply["continuity"]<1 and history_now is not None and len(history_now)>=10:
                logger.info(f"Episodic memory is being created due to continuity: {main_reply['continuity']}")
                parse_episodic_memory(user_id,state_store,vector_store,llm)
                state_store.reset_conversation(user_id)
            emotional_state.recalculate_states(stimuli_tag_data_user,stimuli_tag_data_ai)
            state_store.update_conversation_history(user_id,"user",transcript,main_reply["continuity"])
            state_store.update_conversation_history(user_id,"ai",main_reply["response"],main_reply["continuity"])
            return {
                "transcript":transcript,
                "response":main_reply["response"],
                "metrics":state_store.get_current_metrics(user_id)
            }
    except Exception:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,detail="An error occured while processing the request")


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
