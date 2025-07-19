#!/usr/bin/env python3
"""Add demo transactions directly to database for better search functionality demonstration."""

import asyncio
from datetime import datetime

from src.lanabot.database import DatabaseManager


async def add_demo_transactions():
    """Add sample transactions directly via database manager."""
    db = DatabaseManager()
    
    # Use a demo phone number
    demo_phone = "5215512345678"
    
    # Sample transaction data with common search terms
    demo_data = [
        # Mercancía (inventory/merchandise)
        {"phone_number": demo_phone, "transaction_type": "gasto", "amount": 500.00, "description": "mercancía para la tienda"},
        {"phone_number": demo_phone, "transaction_type": "gasto", "amount": 300.50, "description": "surtido de mercancía OXXO"},
        
        # Refrescos (soft drinks)
        {"phone_number": demo_phone, "transaction_type": "venta", "amount": 45.00, "description": "3 refrescos coca cola"},
        {"phone_number": demo_phone, "transaction_type": "gasto", "amount": 120.00, "description": "caja de refrescos"},
        
        # Dulces (candy)
        {"phone_number": demo_phone, "transaction_type": "venta", "amount": 25.50, "description": "dulces variados"},
        {"phone_number": demo_phone, "transaction_type": "gasto", "amount": 80.00, "description": "dulces para vender"},
        
        # Cigarros
        {"phone_number": demo_phone, "transaction_type": "venta", "amount": 60.00, "description": "cajetilla de cigarros"},
        
        # Papitas/snacks
        {"phone_number": demo_phone, "transaction_type": "venta", "amount": 15.00, "description": "papitas sabritas"},
        {"phone_number": demo_phone, "transaction_type": "gasto", "amount": 90.00, "description": "papitas y botanas"},
        
        # Initial cash
        {"phone_number": demo_phone, "transaction_type": "venta", "amount": 1000.00, "description": "saldo inicial del día"},
    ]
    
    print(f"Adding {len(demo_data)} demo transactions for {demo_phone}...")
    
    for data in demo_data:
        try:
            # Insert directly using Supabase client
            data["created_at"] = datetime.utcnow().isoformat()
            result = db.client.table("transactions").insert(data).execute()
            
            if result.data:
                transaction = result.data[0]
                print(f"✅ Added: {transaction['transaction_type']} ${transaction['amount']} - {transaction['description']}")
            else:
                print(f"❌ Failed to add: {data}")
                
        except Exception as e:
            print(f"❌ Error adding transaction: {e}")
    
    print("\n📊 Demo data added successfully!")
    print(f"🔍 Now you can test searches like:")
    print("- '¿cuánto gasté en mercancía?'")
    print("- '¿cuánto vendí de refrescos?'")
    print("- '¿cuánto gasté en dulces?'")
    print("- 'mis ventas de papitas'")
    print(f"\n📱 Use phone number: {demo_phone}")


if __name__ == "__main__":
    asyncio.run(add_demo_transactions())