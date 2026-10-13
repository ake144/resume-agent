"""Local and international source catalog.

Sources without a documented permitted API are link/paste sources. The app
can preserve and analyze a user-provided posting without crawling or bypassing
access controls.
"""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SourcePreset:
    provider: str
    label: str
    region: str
    homepage: str
    mode: str
    notes: str


SOURCE_PRESETS = (
    SourcePreset(
        provider="ethiojobs_manual",
        label="Ethiojobs",
        region="Ethiopia",
        homepage="https://ethiojobs.net/jobs",
        mode="link_or_paste",
        notes="Analyze a job URL or paste the posting; no automated crawling.",
    ),
    SourcePreset(
        provider="hahu_manual",
        label="HaHuJobs",
        region="Ethiopia",
        homepage="https://www.hahu.jobs/",
        mode="link_or_paste",
        notes="Analyze a job URL or forwarded posting; no automated crawling.",
    ),
    SourcePreset(
        provider="harmee_manual",
        label="Harmee Jobs",
        region="Ethiopia",
        homepage="https://harmeejobs.com/",
        mode="link_or_paste",
        notes="Manual link or paste only while access verification is present.",
    ),
    SourcePreset(
        provider="linkedin_manual",
        label="LinkedIn Jobs",
        region="International",
        homepage="https://www.linkedin.com/jobs/",
        mode="link_or_paste",
        notes="Use a user-provided public job URL or copied posting content.",
    ),
    SourcePreset(
        provider="telegram_manual",
        label="Telegram job channels",
        region="Local and international",
        homepage="https://telegram.org/",
        mode="forward_or_paste",
        notes="Forward or paste a permitted channel post; never read private channels without authorization.",
    ),
)


def list_source_presets() -> list[dict]:
    return [asdict(preset) for preset in SOURCE_PRESETS]
