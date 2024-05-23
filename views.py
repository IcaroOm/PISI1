from fastapi import APIRouter, HTTPException
import requests
import json
import random
import string

router = APIRouter()


def generate_random_password(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


@router.get('/generate_password/')
def generate_password(length: int):
    if length < 1:
        raise HTTPException(
            status_code=400, detail='Length must be greater than zero'
        )
    return {'password': generate_random_password(length)}


def check_pwned_email(email):
    response = requests.get(f'https://leakcheck.io/api/public?check={email}')

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail='Failed to retrieve data from Have I Been Pwned API.',
        )

    data_str = response.text
    data_json = json.loads(data_str)
    print(data_json)

    return data_json


@router.get('/check_email/')
def check_email(email: str):
    data = check_pwned_email(email)
    if data['found'] == 0:
        return {
            'message': 'Your email has not been found in any data breaches.'
        }
    else:
        sources = data['sources']
        count = data['found']
        return dict(
            message=f'Your email has been found in {count} data breaches.',
            sources=sources,
        )
