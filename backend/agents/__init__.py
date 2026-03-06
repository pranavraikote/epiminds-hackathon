from agents.scavenger_market import ScavengerMarket
from agents.scavenger_social import ScavengerSocial
from agents.strategist import Strategist
from agents.forager import Forager
from agents.mutator import Mutator
from agents.audience_sniper import AudienceSniper

all_agents = [
    ScavengerMarket(),
    ScavengerSocial(),
    Strategist(),
    Forager(),
]

mutator_agent = Mutator()
audience_sniper_agent = AudienceSniper()
