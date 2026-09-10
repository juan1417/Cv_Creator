from pydantic import BaseModel, Field
from typing import List, Optional


class Experience(BaseModel):
    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: Optional[str] = None
    description: str = ""


class Education(BaseModel):
    degree: str = ""
    institution: str = ""
    start_date: str = ""
    end_date: Optional[str] = None
    description: str = ""


class Achievement(BaseModel):
    title: str = ""
    description: str = ""


class Language(BaseModel):
    name: str = ""
    level: str = ""


class CvData(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    about: str = ""
    linkedin: str = ""
    portfolio: str = ""
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
    programs: List[str] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
