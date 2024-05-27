from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import db
import os
from openai import OpenAI

openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

app = FastAPI()
client = db.supabase

# Models
class Character(BaseModel):
    name: str
    details: str

def check_for_character(id: int):
    response = client.table('characters').select('*').eq('id', id).execute()
    if not response.data:
        return False, response
    return True, response

# Endpoint to create a character
@app.post("/api/create_character/", status_code=201)
async def create_character(character: Character):
    data, _ = client.table('characters').insert({"name": character.name.lower(), "details": character.details}).execute()
    return {
        "message": "Character created/updated successfully", 
        "data": data, 
    }

# Endpoint to generate a story
@app.get("/api/generate_story/{character_id}", status_code=201)
async def generate_story(character_id: Optional[int] = None):
    if character_id is None:
       raise HTTPException(status_code=404, detail="No id available") 

    # check if the character exists in db
    check, response = check_for_character(character_id)
    if check == False:
        return {"message": "character does not exist"}

    # use the details to generate a story using openai completions api
    character_name = response.data[0].get('name')
    details = response.data[0].get('details')

    prompt = f""" Create a short story for a character name this is given below, using the details
    of the character also given below. An example is supplied, 

    Example: 
    Character name: Bilbo 
    Details: Hobbit lives in the Shire owning a magic ring 
    
    Response: Bilbo, a cheerful Hobbit, lived a quiet life in the peaceful land of the
    Shire. Unbeknownst to many, he owned a mysterious magic ring, which he
    stumbled upon during one of his adventures. This ring granted him the ability
    to become invisible, a secret he kept close to his heart. Though content with
    his simple life, Bilbo often daydreamed about the adventures the ring could
    lead him to. Little did he know, destiny had grand plans for him and his
    magical possession.

    Character name: {character_name}
    Details: {details}
    """
    openai_response = openai_client.Completion.create(
        model="gpt-3.5-turbo-instruct",  # Use the appropriate model
        prompt=prompt,
        # max_tokens=200
    )

    story = openai_response.choices[0].text.strip()
    return {"message": story}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

