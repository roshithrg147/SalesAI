from pydantic import BaseModel, Field
from typing import Optional

class AgentDecision(BaseModel):
    intent: str = Field(description="Is the user asking for price, size, or ready to buy?")
    response_text: str = Field(description="The actual message to send to the customer.")
    product_id: Optional[str] = None
    needs_human: bool = False # Flag if the AI is confused