-- LanaBot Database Schema for Supabase
-- Execute this in your Supabase SQL editor

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('venta', 'gasto')),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_transactions_phone_number ON transactions(phone_number);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS update_transactions_updated_at ON transactions;
CREATE TRIGGER update_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) - optional but recommended
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users (if using Supabase auth)
-- Uncomment if you plan to add authentication later
-- CREATE POLICY "Users can manage their own transactions" ON transactions
--     FOR ALL USING (auth.uid() = user_id::uuid);

-- Insert some sample data for testing (optional)
-- Uncomment to add test data
-- INSERT INTO transactions (phone_number, transaction_type, amount, description) VALUES
-- ('+5215551234567', 'venta', 45.00, '3 coca colas a 15 pesos'),
-- ('+5215551234567', 'gasto', 200.00, 'mercancía del súper'),
-- ('+5215551234567', 'venta', 24.00, '2 sabritas de 12 pesos');

-- Verify table creation
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'transactions'
ORDER BY ordinal_position;