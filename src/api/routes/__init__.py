"""BrainForge AI Knowledge Base - API routes package."""

from .agent import router as agent_router
from .auth import router as auth_router
from .gdpr import router as gdpr_router
from .ingestion import router as ingestion_router
from .monitoring import router as monitoring_router
from .notes import router as notes_router
from .obsidian import router as obsidian_router
from .quality import router as quality_router
from .research import router as research_router
from .search import router as search_router
from .vault import router as vault_router

# Export the routers for easy access
agent = agent_router
auth = auth_router
gdpr = gdpr_router
ingestion = ingestion_router
monitoring = monitoring_router
notes = notes_router
obsidian = obsidian_router
quality = quality_router
research = research_router
search = search_router
vault = vault_router
