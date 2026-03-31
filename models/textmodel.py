from pydantic import BaseModel, Field
class TextModel(BaseModel):
    user : str = Field(..., description="The user who created the text")
    text : str = Field(..., description="The text content to be checked for grammar issues")

class CompareModel(BaseModel):
    text1: str = Field(..., description="Original/Source text")
    text2: str = Field(..., description="Suspect/Comparison text")
    user: str = Field("anonymous", description="User ID")


