__all__ = ['Song']

from typing import Optional

from pydantic.v1 import BaseModel, Field


class TitleLocalized(BaseModel):
    en: str
    jp: Optional[str]
    kr: Optional[str]
    zh_Hans: Optional[str] = Field(str, alias='zh-Hans')
    zh_Hant: Optional[str] = Field(str, alias='zh-Hant')


class SourceLocalized(BaseModel):
    en: str
    ja: Optional[str]
    kr: Optional[str]
    zh_Hans: Optional[str] = Field(str, alias='zh-Hans')
    zh_Hant: Optional[str] = Field(str, alias='zh-Hant')


class BgDayNight(BaseModel):
    day: str
    night: str


class Difficulty(BaseModel):
    ratingClass: int
    chartDesigner: str
    jacketDesigner: str
    jacketOverride: Optional[bool]
    rating: int
    ratingPlus: Optional[bool]


class Song(BaseModel):
    idx: int
    id: str
    title_localized: TitleLocalized
    source_localized: Optional[SourceLocalized]
    source_copyright: Optional[str]
    artist: str
    bpm: str
    bpm_base: float
    set: str
    purchase: str
    audioPreview: int
    audioPreviewEnd: int
    side: int
    bg: str
    bg_daynight: Optional[BgDayNight]
    bg_inverse: Optional[str]
    remote_dl: Optional[bool]
    date: int
    version: str
    difficulties: list[Difficulty]


class ChartBpmDescriptionItem(BaseModel):
    bpm: float
    start_time: int
    end_time: Optional[int]


class ChartBpmDescription(BaseModel):
    base_bpm_override: Optional[float]
    items: list[ChartBpmDescriptionItem]
