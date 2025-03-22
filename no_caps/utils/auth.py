from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

config_data = {
    "AUTH0_DOMAIN": "your-auth0-domain",
    "AUTH0_CLIENT_ID": "your-auth0-client-id",
    "AUTH0_CLIENT_SECRET": "your-auth0-client-secret",
    "AUTH0_AUDIENCE": "your-auth0-api-audience",
}
config = Config(environ=config_data)
oauth = OAuth(config)

oauth.register(
    name="auth0",
    client_id=config_data["AUTH0_CLIENT_ID"],
    client_secret=config_data["AUTH0_CLIENT_SECRET"],
    authorize_url=f"https://{config_data['AUTH0_DOMAIN']}/authorize",
    authorize_params=None,
    access_token_url=f"https://{config_data['AUTH0_DOMAIN']}/oauth/token",
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=None,
    client_kwargs={"scope": "openid profile email"},
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://{config_data['AUTH0_DOMAIN']}/authorize",
    tokenUrl=f"https://{config_data['AUTH0_DOMAIN']}/oauth/token",
)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_email = payload.get("email")
        if user_email is None:
            print("utils/auth.py: get_current_user - Invalid token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_email
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")