-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK (role IN ('borrower', 'underwriter', 'admin')) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    document_name TEXT NOT NULL,
    document_content BYTEA,
    document_type TEXT,
    parsed_data JSONB,
    uploaded_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE rule_evaluation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    document_id UUID REFERENCES documents(id),
    rule_values JSONB NOT NULL,  -- summary of all rule evaluations
    rule_status TEXT CHECK (rule_status IN ('pass', 'fail')) NOT NULL,
    evaluated_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE ml_prediction_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    document_id UUID REFERENCES documents(id),
    predicted_decision TEXT CHECK (predicted_decision IN ('accepted', 'rejected')) NOT NULL,
    confidence_score FLOAT NOT NULL,
    shap_summary JSONB,
    evaluated_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE fairness_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ml_result_id UUID REFERENCES ml_prediction_results(id),
    bias_detected BOOLEAN NOT NULL,
    flagged_fields JSONB,
    audit_summary TEXT,
    audited_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE decision_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT CHECK (type IN ('auto', 'override')) NOT NULL,
    borrower_id UUID REFERENCES users(id),
    underwriter_id UUID REFERENCES users(id),
    ml_result_id UUID REFERENCES ml_prediction_results(id),
    rule_result_id UUID REFERENCES rule_evaluation_log(id),
    fairness_audit_log_id UUID REFERENCES fairness_audit_log(id),
    final_decision TEXT CHECK (final_decision IN ('approved', 'rejected', 'pending_biased', 'pending_conflict', 'error', 'escalated')) NOT NULL,
    document_id UUID REFERENCES documents(id),
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE shadow_model_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    overridden_by UUID REFERENCES users(id),
    reason TEXT NOT NULL,
    model_gap_summary JSONB,  -- explainable factors or feature drift
    included_in_training BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE rules_config (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    field TEXT NOT NULL,
    operator TEXT NOT NULL,  -- e.g., '>=', '<', '=', '!=', 'in', 'not in'
    value TEXT NOT NULL,     -- Stored as text, parsed based on field type
    message TEXT             -- Optional failure message
);

CREATE TABLE training_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    salary NUMERIC NOT NULL,
    credit_score INTEGER NOT NULL,
    employment_years INTEGER NOT NULL,
    loan_amount NUMERIC NOT NULL,
    target INTEGER NOT NULL CHECK (target IN (0,1)),
    source TEXT DEFAULT 'manual_override',
    added_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS explanation_letters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id VARCHAR(100),
    decision_id VARCHAR(100),
    letter_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


-- INSERT INTO training_data (salary, credit_score, employment_years, loan_amount, target, source) VALUES
-- (60000, 720, 5, 200000, 1, 'INITIAL_LOAD'),
-- (45000, 680, 2, 150000, 0, 'INITIAL_LOAD'),
-- (85000, 750, 7, 250000, 1, 'INITIAL_LOAD'),
-- (32000, 610, 1, 120000, 0, 'INITIAL_LOAD'),
-- (70000, 730, 4, 180000, 1, 'INITIAL_LOAD'),
-- (40000, 640, 1, 100000, 0, 'INITIAL_LOAD'),
-- (55000, 700, 3, 160000, 1, 'INITIAL_LOAD');


-- -- Password hash for 'password' using bcrypt
-- INSERT INTO users (full_name, email, password_hash, role)
-- VALUES 
--   ('John Borrower', 'borrower1@example.com', '$2b$12$Z6c3pHL5zdaqlStD25Zp8.G7dkOknuDwRrgQUiVUpjCn9hpoLtMOK', 'borrower'),
--   ('Jane Underwriter', 'underwriter1@example.com', '$2b$12$Z6c3pHL5zdaqlStD25Zp8.G7dkOknuDwRrgQUiVUpjCn9hpoLtMOK', 'underwriter');

-- INSERT INTO rules_config (name, field, operator, value, message) VALUES
-- ('Salary Check', 'salary', '>=', '50000', 'Salary too low'),
-- ('Employer Check', 'employer', 'not in', 'fraud inc, unknown corp', 'Blacklisted employer');