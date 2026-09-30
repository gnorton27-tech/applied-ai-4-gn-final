#!/usr/bin/env python
"""
Tournament Agent: Strategic Retaliator
Student: GraceNorton
Generated: 2026-09-29 21:34:04

Evolution Details:
- Generations: 100
- Final Fitness: N/A
- Trained against: Grim Trigger, Always Undercut, Adaptive, Suspicious Tit-for-Tat, Pavlov...

Strategy: Adapts to recent opponent behavior, cooperating with cooperative opponents and retaliating against repeated undercutting.
"""

from agents import Agent, INVEST, UNDERCUT
import random


class GraceNortonAgent(Agent):
    """
    Strategic Retaliator
    
    Adapts to recent opponent behavior, cooperating with cooperative opponents and retaliating against repeated undercutting.
    
    Evolved Genes: [0.7856564142684666, 1.0, 0.600963591498769, 0.0, 0.14969035801656128, 0.8334094626309467]
    """
    
    def __init__(self):
        # These genes were evolved through 100 generations
        self.genes = [0.7856564142684666, 1.0, 0.600963591498769, 0.0, 0.14969035801656128, 0.8334094626309467]
        
        # Required for tournament compatibility
        self.student_name = "GraceNorton"
        
        super().__init__(
            name="Strategic Retaliator",
            description="Adapts to recent opponent behavior, cooperating with cooperative opponents and retaliating against repeated undercutting."
        )
    
    def choose_action(self) -> bool:
        """
        IMPROVED decision logic - AGGRESSIVE VERSION
        More likely to retaliate, less exploitable
        """
        
        # First 3 rounds: use initial cooperation gene
        if self.round_num < 3:
            return random.random() < self.genes[0]
        
        # Calculate memory window
        memory_length = max(1, int(self.genes[4] * 10) + 1)
        recent_history = self.history[-memory_length:]
        cooperation_rate = sum(recent_history) / len(recent_history)
        
        # AGGRESSIVE STRATEGY: Higher threshold for cooperation
        
        # Only cooperate if opponent is VERY cooperative (>80%)
        if cooperation_rate > 0.8:
            return random.random() < self.genes[1]  # gene[1] should evolve HIGH
        
        # If somewhat cooperative (50-80%), be cautious
        elif cooperation_rate > 0.5:
            # Mix of cooperation and defection
            coop_prob = self.genes[1] * (cooperation_rate - 0.5) * 2  # Scale 0-1
            return random.random() < coop_prob
        
        # If aggressive (<50%), retaliate hard
        else:
            # Mostly defect, with small chance to forgive
            if random.random() < self.genes[3] * 0.3:  # Reduced forgiveness
                return INVEST
            else:
                return UNDERCUT



# Convenience function for tournament loading
def get_agent():
    """Return an instance of this agent for tournament use"""
    return GraceNortonAgent()


if __name__ == "__main__":
    # Test that the agent can be instantiated
    agent = get_agent()
    print(f"✅ Agent loaded successfully: {agent.name}")
    print(f"   Genes: {agent.genes}")
    print(f"   Description: {agent.description}")
