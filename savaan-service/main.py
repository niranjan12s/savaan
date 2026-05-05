from fastapi import FastAPI, HTTPException, status, Depends,File,UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from auth import hash_password,create_access_token
from auth import pwd_context
from fastapi.middleware.cors import CORSMiddleware
import os
from transcriber import transcribe_audio
import uvicorn
from middleware import request
from logger import logger
from model import models
from emotional_engine import generate_emotional_summary
from emotional_state import *
import chromadb
from episodic_memory import fetch_from_episodic_memory,create_episodic_memory
from conversation_history import get_conversation_history,reset_conversation,update_conversation_history
from central_response_generator import generate_reply

models.init_db()
chroma_client = chromadb.PersistentClient(path="./chroma_storage")
episodic_memory=chroma_client.get_or_create_collection(name="episodic_memory")


app=FastAPI()
app.add_middleware(request.RequestIdMiddleWare)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        with next(get_session()) as session:
            #return get_conversation_history(user_id,session)
            transcript=transcribe_audio(file_path)
            logger.info(f"Transcription completed: {transcript}")
            stimuli_tag_data_user=generate_emotional_summary(transcript)
            logger.info(f"tags: {stimuli_tag_data_user}")
            emotional_state=EmotionalStateManager(user_id,session=session)
            logger.info(f"Conversation_history: {get_conversation_history(user_id,session)}")
            episodic_results=fetch_from_episodic_memory(user_id,transcript,stimuli_tag_data_user,session,episodic_memory)
            logger.info(f"Episodic Results : {episodic_results}")
            main_reply=generate_reply(transcript,get_current_dopamine_and_survival(user_id,session),
                        get_dopamine_and_survival_history(user_id,session),
                        get_conversation_history(user_id,session),
                        episodic_results["documents"])
            stimuli_tag_data_ai=generate_emotional_summary(main_reply["response"])
            logger.info(f"tags: {stimuli_tag_data_ai}")
            if main_reply["continuity"]<1 and get_conversation_history(user_id,session)is not None and get_conversation_history(user_id,session)>=10:
                logger.info(f"Episodic memory is being created due to continuity: {main_reply['continuity']}")
                create_episodic_memory(user_id,session)
                reset_conversation(user_id,session)
            emotional_state.recalculate_states(stimuli_tag_data_user,stimuli_tag_data_ai,session)
            update_conversation_history(user_id,"user",transcript,main_reply["continuity"],session)
            update_conversation_history(user_id,"ai",main_reply["response"],main_reply["continuity"],session)
            return {
                "transcript":transcript,
                "response":main_reply["response"],
                "metrics":get_current_dopamine_and_survival(user_id,session)
            }
    except Exception:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,detail="An error occured while processing the request")


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
