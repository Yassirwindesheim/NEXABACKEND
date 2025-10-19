# app/routers/workorders.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # 🌟 Imported for eager loading
import uuid # 🌟 ADD THIS IMPORT 🌟

from app.db import get_session
from app.models import Workorder
from app.schemas import WorkorderCreate, WorkorderOut
from app.deps import get_current_user, AuthedUser


router = APIRouter(prefix="/workorders", tags=["workorders"])


import logging
# Add this line at the top of the file
log = logging.getLogger(__name__)

@router.get("", response_model=list[WorkorderOut])
async def list_workorders(
    user: AuthedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    status: Optional[str] = None,
):
    # This log MUST appear if authentication succeeded
    log.info(f"Starting list_workorders request. Status filter: {status}") 
    
    q = (
        select(Workorder)
        .options(selectinload(Workorder.customer))
        .order_by(Workorder.created_at.desc())
    )
    
    if status:
        q = q.where(Workorder.status == status)

    res = await db.execute(q)
    workorders = res.scalars().unique().all()
    
    log.info(f"Successfully fetched {len(workorders)} workorders from the database.")
    
    # 🌟 DEFINITIVE FIX: Pre-process the list to ensure Pydantic doesn't use the session 🌟
    output = []
    for w in workorders:
        
        # Safely handle potential NULL customer relationship
        customer_name = w.customer.name if w.customer else "N/A"
        customer_phone = w.customer.phone if w.customer else None

        # Build the dictionary that Pydantic will use (safely detached from the ORM session)
        output.append(
            {
                "id": w.id,
                "vehicle": w.vehicle,
                "customer": customer_name, 
                "phone": customer_phone,
                "received": w.received,
                "due": w.due,
                "complaint": w.complaint,
                "status": w.status.value,
            }
        )
        
    log.info("Successfully created dictionary list. Returning to FastAPI.")
    
    return output



@router.post("", response_model=WorkorderOut, status_code=201)
async def create_workorder(
    payload: WorkorderCreate,
    user: AuthedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):

    generated_id = str(uuid.uuid4())[:8] # Generate a short, unique ID string

    insert_data = payload.model_dump()
    insert_data['id'] = generated_id # Add the generated ID to the insert data

    stmt = (
        insert(Workorder)
        .values(**insert_data) # Use the data with the ID
        .returning(Workorder)
    )
    res = await db.execute(stmt)
    w = res.scalar_one() # Get the newly created object

    # 2. Commit the changes
    await db.commit()
    
    # 3. Load the Workorder again, explicitly eagerly loading the customer 
    # (The necessary step to load the relationship data for the response)
    q = (
        select(Workorder)
        .where(Workorder.id == w.id)
        .options(selectinload(Workorder.customer))
    )
    
    res = await db.execute(q)
    w_loaded = res.scalar_one() 

    # 4. Handle NULL customer (safety check)
    if not w_loaded.customer:
         raise HTTPException(
             status_code=500, 
             detail=f"Customer ID {w_loaded.customer_id} not found after creation."
         )

    # 5. Return the fully loaded object
    return WorkorderOut(
        id=w_loaded.id, # Now this ID is a value, not null
        vehicle=w_loaded.vehicle,
        customer=w_loaded.customer.name,
        phone=w_loaded.customer.phone,
        received=w_loaded.received,
        due=w_loaded.due,
        complaint=w_loaded.complaint,
        status=w_loaded.status.value,
    )

@router.patch("/{workorder_id}", response_model=WorkorderOut)
async def update_workorder(
    workorder_id: str, 
    payload: WorkorderCreate,
    user: AuthedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    res = await db.execute(
        update(Workorder)
        .where(Workorder.id == workorder_id)
        .values(**payload.model_dump(exclude_unset=True)) # Use exclude_unset for PATCH
        .returning(Workorder)
    )
    await db.commit()
    w = res.scalar_one_or_none()

    if not w:
        raise HTTPException(status_code=404, detail="Work order not found")

    # 🌟 FIX: Manually refresh the relationship after commit for the return object
    # Use selectinload to ensure 'customer' is loaded before serialization
    await db.execute(select(Workorder).where(Workorder.id == w.id).options(selectinload(Workorder.customer)))
    await db.refresh(w)

    return WorkorderOut(
        id=w.id,
        vehicle=w.vehicle,
        customer=w.customer.name,
        phone=w.customer.phone,
        received=w.received,
        due=w.due,
        complaint=w.complaint,
        status=w.status.value,
    )