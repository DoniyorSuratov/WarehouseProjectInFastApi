from fastapi import Depends

from auth.utils import verify_token
from database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from fastapi.exceptions import HTTPException

from models.models import Users


async def is_admin(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail="You don't have permission to perform this action to perform action ask admin.")
    user_id = token.get('user_id')
    query = select(Users).where(Users.id == user_id)
    user_data = await session.execute(query)
    try:
        user = user_data.scalar()
        if user.role_id == 1:
            return token
        else:
            raise HTTPException(status_code=403, detail="You don't have permission to perform this action")
    except NoResultFound:
        raise HTTPException(status_code=400, detail="User not found")