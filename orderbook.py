import numpy as np
import pandas as pd
from collections import *
from datetime import *

class OrderBookSimulator():
    def __init__(self, initial_price=662.57, tick_size=0.01):
        self.initial_price = initial_price
        self.current_price = initial_price
        self.tick_size = tick_size
        self.max_levels = 50  # Number of levels in order book (L3)
        
        # Order book structure: price -> volume
        self.bids = OrderedDict()  # Sorted descending
        self.asks = OrderedDict()  # Sorted ascending
        
        # Market microstructure parameters
        self.volatility = 0.16  # Daily volatility
        self.mean_reversion_speed = 0.2
        self.volume_intensity = 1_000  # Base volume intensity
        self.spread_target = 0.0001  # Target spread as % of price
        
        # State variables
        self.last_price = initial_price
        self.momentum = 0.0
        self.tick_count = 0

        # Data storage
        self.price_history = []
        self.spread_history = []
        self.volume_history = []
        self.timestamp_history = []
        self.bids_history = []
        self.bids_volume_history = []
        self.asks_history = []
        self.asks_volume_history = []
        self.mid_history = []
        
    def generate_price_change(self, dt=1/252/24/60/60):  # 1 sec intervals
        """Generate price change using mean-reverting process with momentum"""
        # Mean reversion component
        mean_reversion = -self.mean_reversion_speed * (self.current_price - self.initial_price) * dt
        
        # Random walk component with volatility clustering
        vol_scaling = 1 + 0.3 * abs(self.momentum)  # Higher vol during trending moves
        random_shock = np.random.normal(0, self.volatility * np.sqrt(dt) * vol_scaling)
        
        # Momentum decay
        self.momentum *= 0.95
        
        # Price change
        price_change = mean_reversion + random_shock * self.current_price
        self.momentum += price_change / self.current_price
        
        return price_change
    
    def generate_volume(self, distance_from_mid):
        """Generate volume based on distance from mid price"""
        # Exponential decay with distance + random component
        base_volume = self.volume_intensity * np.exp(-distance_from_mid * 50)
        noise = np.random.exponential(0.3)
        return max(int(base_volume * noise), 10)
    
    def update_price(self):
        """Update the current mid price"""
        price_change = self.generate_price_change()
        self.current_price = max(self.current_price + price_change, 0.01)
        self.last_price = self.current_price
    
    def calculate_target_spread(self):
        """Calculate target bid-ask spread"""
        base_spread = self.spread_target * self.current_price
        volatility_adjustment = abs(self.momentum) * self.current_price * 2
        return max(base_spread + volatility_adjustment, self.tick_size * 2)
    
    def generate_order_book_levels(self):
        """Generate realistic order book levels around current price"""
        target_spread = self.calculate_target_spread()
        
        # Clear existing orders
        self.bids.clear()
        self.asks.clear()
        
        # Generate bid levels (below mid price)
        mid_price = self.current_price
        best_bid = mid_price - target_spread / 2
        
        for i in range(self.max_levels):
            # Price levels with some randomness
            level_spacing = target_spread * (0.1 + 0.05 * np.random.exponential(1))
            bid_price = best_bid - i * level_spacing
            bid_price = round(bid_price / self.tick_size) * self.tick_size
            
            if bid_price > 0:
                distance = abs(bid_price - mid_price) / mid_price
                volume = self.generate_volume(distance)
                self.bids[bid_price] = volume
        
        # Generate ask levels (above mid price)
        best_ask = mid_price + target_spread / 2
        
        for i in range(self.max_levels):
            level_spacing = target_spread * (0.1 + 0.05 * np.random.exponential(1))
            ask_price = best_ask + i * level_spacing
            ask_price = round(ask_price / self.tick_size) * self.tick_size
            
            distance = abs(ask_price - mid_price) / mid_price
            volume = self.generate_volume(distance)
            self.asks[ask_price] = volume
        
        # Sort order books
        self.bids = OrderedDict(sorted(self.bids.items(), reverse=True))
        self.asks = OrderedDict(sorted(self.asks.items()))
    
    def get_best_bid_ask(self):
        """Get best bid and ask prices"""
        if self.bids and self.asks:
            best_bid = max(self.bids.keys())
            best_ask = min(self.asks.keys())
            return best_bid, best_ask
        return None, None
    
    def get_spread(self):
        """Calculate current bid-ask spread"""
        best_bid, best_ask = self.get_best_bid_ask()
        if best_bid and best_ask:
            return best_ask - best_bid
        return 0
    
    def get_total_volume(self):
        """Get total volume on both sides"""
        bid_volume = sum(self.bids.values()) if self.bids else 0
        ask_volume = sum(self.asks.values()) if self.asks else 0
        return bid_volume + ask_volume


    def simulate_tick(self):
        """Simulate one market tick"""
        self.tick_count += 1
        
        # Update price based on financial model
        self.update_price()
        
        # Generate new order book levels
        self.generate_order_book_levels()
        
        # Record data
        timestamp = datetime.now() + timedelta(seconds=self.tick_count)
        self.timestamp_history.append(timestamp)
        self.price_history.append(self.current_price)
        self.spread_history.append(self.get_spread())
        self.volume_history.append(self.get_total_volume())
        self.bids_history.append(max(self.bids.keys()))
        self.bids_volume_history.append(sum(self.bids.values()) if self.bids else 0)
        self.asks_history.append(min(self.asks.keys()))
        self.asks_volume_history.append(sum(self.asks.values()) if self.bids else 0)
        self.mid_history.append(self.current_price)

    
    def display_order_book(self, levels=5):
        """Display current order book"""
        print(f"\n=== Order Book (Tick {self.tick_count}) ===")
        print(f"Mid Price: ${self.current_price:.4f}")
        print(f"Spread: ${self.get_spread():.4f}")
        print("\nASKS:")
        
        ask_items = list(self.asks.items())[:levels]
        for price, volume in reversed(ask_items):
            print(f"  ${price:8.4f} | {volume:6,d}")
        
        print("  " + "-" * 20)
        
        print("BIDS:")
        bid_items = list(self.bids.items())[:levels]
        for price, volume in bid_items:
            print(f"  ${price:8.4f} | {volume:6,d}")
    
    def run_simulation(self, num_ticks):
        display_interval = num_ticks / 10
        
        """Run the full simulation"""
        print(f"Starting Order Book Simulation...")
        print(f"Initial Price: ${self.initial_price}")
        print(f"Simulating {num_ticks} ticks...")
        
        for tick in range(num_ticks):
            self.simulate_tick()
            
            # Display order book at intervals
            if tick % display_interval == 0 or tick == num_ticks - 1:
                self.display_order_book()
        
        print(f"\nSimulation Complete!")
        self.get_results()
    
    def get_results(self):

        # Print summary statistics
        print(f"\n=== Simulation Summary ===")
        print(f"Total Ticks: {len(self.price_history)}")
        print(f"Price Range: ${min(self.price_history):.4f} - ${max(self.price_history):.4f}")
        print(f"Final Price: ${self.price_history[-1]:.4f}")
        print(f"Average Spread: ${np.mean(self.spread_history):.4f}")
        print(f"Average Volume: {np.mean(self.volume_history):,.0f}")


def activate(adjust=True):

    # Create and run simulation
    simulator = OrderBookSimulator(
        initial_price=600.29,
        tick_size=0.01,
    )
        
    # Run simulation
    simulator.run_simulation(num_ticks=22_727) # 22 thousand ticks, ~ 1 day of trading
    df = pd.DataFrame({
                'datetime': simulator.timestamp_history,
                'price': simulator.price_history,
                'spread': simulator.spread_history,
                'bid volume': simulator.bids_volume_history,
                'bid': simulator.bids_history,
                'mid': simulator.mid_history,
                'ask': simulator.asks_history,
                'ask volume': simulator.asks_volume_history,
                'volume': simulator.volume_history,
    })
    
    return df



df = activate()