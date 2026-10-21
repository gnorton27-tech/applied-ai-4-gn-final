#!/usr/bin/env python3
"""
Skeleton Optimization Agent - Template for students to implement optimization algorithms

IMPORTANT: This is NOT an RL agent - it's a template for 
students to implement their own optimization algorithms (greedy, Hungarian, etc.)

This agent currently makes terrible decisions:
- Random staffing decisions
- No layout optimization 
- Ignores order priorities
- No intelligent assignment logic

Students should replace the naive methods with proper optimization algorithms.
"""

import numpy as np
from typing import Dict, Optional
from .standardized_agents import BaselineAgent

class SkeletonOptimizationAgent(BaselineAgent):
    """
    Template for students to implement their own optimization algorithms.
    
    Students should replace the naive methods with:
    - Economic models for staffing decisions
    - Hungarian algorithm for order assignment  
    - Greedy search for layout optimization
    - Multi-objective optimization techniques
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        
        # Enable unlimited hiring for true economic optimization
        self.env._unlimited_hiring = True
        
        # Students can add their own state tracking here
        self.performance_metrics = []
        self.decision_history = []
        
        # Students can add algorithm parameters here
        # Example: Hungarian algorithm matrices, greedy search parameters, etc.
        self.staffing_parameters = {
            'hire_threshold_ratio': 3.0,
            'fire_threshold_ratio': 2.0,
            'profit_threshold': 0
        }
        
        # Students can implement adaptive parameters that change based on performance
        self.adaptive_optimization_enabled = False
        
    def reset(self):
        """Reset agent state - students should expand this"""
        self.action_history = []
        self.reward_history = []
        # TODO: Reset any neural network states, replay buffers, etc.
    
    def get_action(self, observation: Dict) -> Dict:
        """
        Generate action based on observation.
        Current implementation is intentionally terrible - students should improve!
        """
        
        # Extract basic info from observation
        current_timestep = observation['time'][0]
        financial_state = observation['financial']  # [profit, revenue, costs, burn_rate]
        queue_info = observation['order_queue']
        employee_info = observation['employees']

        
        action = {
            'staffing_action': self._get_naive_staffing_action(financial_state, employee_info),
            'layout_swap': self._get_naive_layout_action(current_timestep),
            'order_assignments': self._get_naive_order_assignments(queue_info, employee_info)
        }
        
        # TODO: Students should implement proper action recording for optimization
        self.action_history.append(action.copy())
        
        return action
    
    def _get_naive_staffing_action(self, financial_state, employee_info) -> int:
        """
        Profit-aware warehouse staffing strategy.
        Balances employee coverage with operating costs.
        """

        current_profit = float(financial_state[0])
        num_employees = int(np.sum(employee_info[:, 0] > 0))
        has_manager = bool(np.any(employee_info[:, 5] == 1))

        # Ensure enough workers for warehouse operations
        if num_employees < 5:
            return 1  # Hire worker

        # Ensure a manager is available for layout decisions
            if not has_manager:
                return 3  # Hire manager

        # Expand staffing when the warehouse is profitable
            if current_profit > 2000 and num_employees < 7:
                return 1  # Hire worker

            # Avoid unnecessary hiring when profits are low
                return 0  # Maintain current staffing

    def _get_naive_layout_action(self, current_timestep) -> list:
        """
        WEEK 1 STEP 1: Layout optimization - students should improve this!
        
        Current problems:
        - Random swaps with no strategic purpose
        - Ignores item co-occurrence patterns
        - No consideration of delivery distances
        - Wastes manager time on pointless moves
        """
        
                # Only optimize every 100 steps
        if current_timestep % 25 != 0:
            return [0, 0]

        grid = self.env.warehouse_grid

        # Get item access frequencies
        frequencies = grid.item_access_frequency
        print("FREQUENCIES:", frequencies)
        
        # Make sure frequency data exists
        if frequencies is None or len(frequencies) == 0:
            return [0, 0]

        # Only consider items that have actually been accessed
        active_frequencies = np.array(
            [freq for freq in frequencies if freq > 0]
        )

        if len(active_frequencies) == 0:
            return [0, 0]

        # Top 25% of accessed items are considered "hot"
        hot_threshold = np.percentile(active_frequencies, 75)

        # Get delivery positions
        delivery_positions = getattr(
            grid,
            "truck_bay_positions",
            [(grid.width // 2, grid.height // 2)]
        )

        # Look for a hot item that would benefit from being moved
        for item_type, frequency in enumerate(frequencies):
            if frequency < hot_threshold or frequency <= 0:
                continue

            # Find where this hot item type is actually stored
            positions = np.argwhere(grid.item_grid == item_type)

            if len(positions) == 0:
                continue

            # Check each warehouse position containing this item type
            for y, x in positions:
                current_pos = (int(x), int(y))

                # Find distance to closest delivery position
                current_distance = min(
                    grid.manhattan_distance(current_pos, delivery_pos)
                    for delivery_pos in delivery_positions
                )

                # Only optimize items more than 3 steps away
                if current_distance <= 3:
                    continue

                better_position = self._find_closer_position(
                    current_pos, delivery_positions
                )

                if better_position is not None:
                    return better_position
        # Phase 2: If no frequency-based improvement found, try co-occurrence clustering
        if current_timestep % 200 == 0:
            cooccurrence_swap = self._find_cooccurrence_swap()
            if cooccurrence_swap:
                return cooccurrence_swap        
        return [0, 0]
    def _find_closer_position(self, current_pos, delivery_positions):
        """
        Greedy neighborhood search for better item placement.

        Searches all storage positions to find the position
        that minimizes distance to delivery points.
        """
        grid = self.env.warehouse_grid

        current_idx = current_pos[1] * grid.width + current_pos[0]

        current_dist = min(
            grid.manhattan_distance(current_pos, delivery_pos)
            for delivery_pos in delivery_positions
        )

        best_idx = None
        best_improvement = 0

        for y in range(grid.height):
            for x in range(grid.width):
                if grid.cell_types[y, x] != 1:
                    continue

                candidate_pos = (x, y)

                candidate_dist = min(
                    grid.manhattan_distance(candidate_pos, delivery_pos)
                    for delivery_pos in delivery_positions
                )

                improvement = current_dist - candidate_dist

                if improvement > best_improvement:
                    best_improvement = improvement
                    best_idx = y * grid.width + x

        if best_idx is not None:
            return [current_idx, best_idx]
    def _find_cooccurrence_swap(self):
        """
        Greedy clustering algorithm for association-based spatial optimization.

        Scans item pairs for clustering opportunities and selects
        the highest-benefit move.
        """
        grid = self.env.warehouse_grid
        cooccurrence = grid.item_cooccurrence

        # Greedy search parameters
        min_cooccurrence = 3
        min_distance = 4
        best_benefit = 0
        best_swap = None

        # Scan item pairs
        num_items = cooccurrence.shape[0]

        for item1 in range(num_items):
            for item2 in range(item1 + 1, num_items):
                cooccurrence_count = cooccurrence[item1, item2]

                # Only consider frequently co-occurring items
                if cooccurrence_count <= min_cooccurrence:
                    continue

                # Find current locations of both items
                locations1 = grid.find_item_locations(item1)
                locations2 = grid.find_item_locations(item2)

                if not locations1 or not locations2:
                    continue

                pos1 = locations1[0]
                pos2 = locations2[0]

                # Calculate current distance between items
                current_distance = grid.manhattan_distance(pos1, pos2)

                # Only cluster items that are sufficiently far apart
                if current_distance <= min_distance:
                    continue

                # Greedy benefit calculation
                benefit = cooccurrence_count * current_distance

                if benefit > best_benefit:
                    # Move item1 adjacent to item2 if possible
                    target_swap = self._find_adjacent_swap(pos1, pos2)

                    if target_swap is not None:
                        best_benefit = benefit
                        best_swap = target_swap

        return best_swap

    def _find_adjacent_swap(self, source_pos, target_pos):
        """
        Find a storage position adjacent to the target item
        and return a swap that moves the source item there.
        """
        grid = self.env.warehouse_grid

        source_idx = source_pos[1] * grid.width + source_pos[0]

        # Check positions directly around the target item
        neighbors = [
            (target_pos[0] + 1, target_pos[1]),
            (target_pos[0] - 1, target_pos[1]),
            (target_pos[0], target_pos[1] + 1),
            (target_pos[0], target_pos[1] - 1),
        ]

        for x, y in neighbors:
            # Make sure position is inside the warehouse
            if x < 0 or x >= grid.width or y < 0 or y >= grid.height:
                continue

            # Only use storage cells
            if grid.cell_types[y, x] != 1:
                continue

            target_idx = y * grid.width + x

            # Don't swap a position with itself
            if target_idx == source_idx:
                continue

            return [source_idx, target_idx]

        return None
    
    def _get_naive_order_assignments(self, queue_info, employee_info) -> list:
        """
        Optimized order assignment strategy.
        Prioritizes valuable orders and distributes work
        across available employees.
        """

        assignments = [0] * 20

        # Identify active employees and waiting orders
        active_employees = np.where(employee_info[:, 0] > 0)[0]
        active_orders = np.where(queue_info[:, 0] > 0)[0]

        if len(active_employees) == 0 or len(active_orders) == 0:
            return assignments

        # Rank orders by value, highest first
        sorted_orders = sorted(
            active_orders,
            key=lambda i: queue_info[i, 1],
            reverse=True
        )

        # Assign each employee to one priority order
        for employee_idx, order_idx in zip(active_employees, sorted_orders):
            if order_idx >= len(assignments):
                continue

            assignments[order_idx] = int(employee_idx) + 1

        return assignments

    def track_layout_performance(self):
        """
        Performance analysis for greedy layout optimization algorithms.
        """
        if not hasattr(self, 'layout_metrics'):
            self.layout_metrics = []

        efficiency = self._calculate_layout_efficiency()

        self.layout_metrics.append({
            'timestep': self.env.current_timestep,
            'efficiency': efficiency
        })

        if self.env.current_timestep % 1000 == 0:
            valid_efficiencies = [
                 m['efficiency']
                for m in self.layout_metrics[-10:]
                 if m['efficiency'] is not None
            ]

            recent_efficiency = np.mean(valid_efficiencies) if valid_efficiencies else 0.0
            print(f"Layout efficiency: {recent_efficiency:.3f}")
    def _calculate_layout_efficiency(self):
        """
        Calculate frequency-weighted layout efficiency.
        Higher values mean frequently accessed items are closer
        to delivery positions.
        """
        grid = self.env.warehouse_grid
        frequencies = grid.item_access_frequency

        if frequencies is None or len(frequencies) == 0:
            return 0.0

        delivery_positions = getattr(
            grid,
            "truck_bay_positions",
            [(grid.width // 2, grid.height // 2)]
        )

        weighted_distance = 0.0
        total_frequency = 0.0

        for item_type, frequency in enumerate(frequencies):
                if frequency <= 0:
                    continue

        locations = grid.find_item_locations(item_type)

        for pos in locations:
                distance = min(
                    grid.manhattan_distance(pos, delivery_pos)
                    for delivery_pos in delivery_positions
                )

                weighted_distance += frequency * distance
                total_frequency += frequency

        if total_frequency == 0:
            return 0.0

        weighted_avg_distance = weighted_distance / total_frequency

        max_possible_distance = grid.width + grid.height

        efficiency = 1.0 - (
            weighted_avg_distance / max_possible_distance
        )

        return max(0.0, min(1.0, efficiency))
    def record_reward(self, reward: float):
        """
        WEEK 3 STEP 1: Reward tracking and learning - students should expand this
        
        TODO WEEK 3 STEP 1: Students should implement:
        - Proper reward tracking
        - Performance analysis
        - Adaptive parameter adjustment
        - Multi-objective optimization
        """
        self.reward_history.append(reward)
        
        # Skeleton optimization - doesn't actually learn anything useful
        if len(self.reward_history) > 10:
            # "Update" weights randomly (this doesn't actually improve performance)
            if reward > 0:
                self.staffing_weights += np.random.randn(4) * 0.01
                self.layout_weights += np.random.randn(3) * 0.01
    
    def should_update_policy(self) -> bool:
        """
        WEEK 3 STEP 2: Policy updates and adaptation - students should improve this
        
        TODO WEEK 3 STEP 2: Students should implement proper update schedules
        """
        return len(self.action_history) % 50 == 0  # Arbitrary update frequency
    
    def get_performance_metrics(self) -> Dict:
        """
        Get agent performance metrics for analysis
        Students can use this to debug their improvements
        """
        if not self.reward_history:
            return {"avg_reward": 0, "total_actions": 0}
        
        return {
            "avg_reward": np.mean(self.reward_history[-100:]),  # Last 100 rewards
            "total_actions": len(self.action_history),
            "exploration_rate": self.exploration_rate,
            "recent_performance": np.mean(self.reward_history[-10:]) if len(self.reward_history) >= 10 else 0
        }


def create_skeleton_optimization_agent(env) -> SkeletonOptimizationAgent:
    """Factory function to create skeleton Optimization agent"""
    return SkeletonOptimizationAgent(env)


# TODO: Students should implement these advanced components:

class StudentOptimizationAgent(SkeletonOptimizationAgent):
    """
    Template for students to implement their improved Optimization agent
    
    Suggested improvements:
    1. Replace random staffing with demand-based hiring
    2. Implement proper layout optimization using item frequencies
    3. Add distance-based order assignment
    4. Implement basic Q-optimization or policy gradients
    5. Add proper exploration vs exploitation balance
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        
        # TODO: Students implement these
        # self.q_table = {}
        # self.policy_network = SimpleNeuralNetwork()
        # self.experience_buffer = []
        # self.target_network = None
        
    def _get_improved_staffing_action(self, financial_state, employee_info, queue_info):
        """
        WEEK 2 STEP 1: Students implement intelligent staffing:
        - Hire when queue is growing
        - Fire when queue is empty for extended periods
        - Consider profit margins before hiring
        - Balance managers vs workers
        """
        pass
    
    def _get_improved_layout_action(self, observation):
        """
        WEEK 1 STEP 1: Students implement smart layout optimization:
        - Move frequently accessed items closer to delivery
        - Group items that are often ordered together
        - Only optimize when queue is manageable
        - Track swap effectiveness
        """
        pass
    
    def _get_improved_order_assignments(self, queue_info, employee_info):
        """
        WEEK 2 STEP 2: Students implement efficient order assignment:
        - Assign orders to closest available employees
        - Prioritize high-value or urgent orders
        - Consider employee current locations
        - Balance workload across employees
        """
        pass
    
    def learn_from_experience(self, state, action, reward, next_state, done):
        """
        WEEK 3 STEP 3: Students implement multi-objective optimization:
        - Performance trend analysis
        - Adaptive parameter tuning
        - Multi-objective trade-off handling
        - Robust optimization techniques
        """
        pass