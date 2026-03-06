from agents.scavenger_market import ScavengerMarket
from agents.scavenger_social import ScavengerSocial
from agents.strategist import Strategist
from agents.forager import Forager
from agents.mutator import Mutator
from agents.audience_sniper import AudienceSniper
from agents.skeptic import Skeptic

all_agents = [
    ScavengerMarket(),
    ScavengerSocial(),
    Forager(),
    Skeptic(),
    Strategist(),
    Mutator(),
    AudienceSniper(),
]

# Singletons for the follow-up fast path (run_followup bypasses the swarm bus)
strategist_agent = Strategist()
mutator_agent = Mutator()
